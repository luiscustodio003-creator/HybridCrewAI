"""Ingestão segura de ZIP para o workspace."""

from __future__ import annotations

import io
import os
import shutil
import stat
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.sensitive import SensitiveFile, classify_bytes, read_attachment_bytes

_STAGING = ".archive-staging"
_MAGICOS_ZIP = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_MODO_LIGACAO = 0o170000


class ArchiveError(ValueError):
    """Arquivo rejeitado ou extração que não pôde ser concluída."""


@dataclass(frozen=True)
class ArchiveLimits:
    """Limites aplicados antes de qualquer extração."""

    max_chars: int
    max_file_bytes: int
    max_total_bytes: int
    max_zip_bytes: int
    max_entries: int
    max_ratio: int
    max_nesting: int


@dataclass(frozen=True)
class ArchiveEntry:
    """Metadados seguros de uma entrada extraída."""

    path: str
    size: int
    sha256: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ArchiveReport:
    """Resultado da ingestão sem expor o conteúdo das entradas."""

    destination: str
    entries: tuple[ArchiveEntry, ...]
    total_bytes: int
    total_compressed: int


@dataclass(frozen=True)
class _Preparado:
    """Entrada validada e pronta para gravação."""

    suffix: Path
    data: bytes
    classified: SensitiveFile


@dataclass(frozen=True)
class _Contexto:
    """Estado partilhado pela validação de entradas."""

    arquivo: zipfile.ZipFile
    raiz: Path
    destino: Path
    limits: ArchiveLimits


def ingest_zip(
    root: Path,
    source: Path,
    *,
    destination: str,
    limits: ArchiveLimits,
) -> ArchiveReport:
    """Valida e extrai um ZIP para o workspace sem confiar no seu conteúdo."""
    _validar_limites(limits)
    raiz = _raiz(root)
    destino = validate_workspace_path(raiz, destination, max_chars=limits.max_chars)
    if destino.exists():
        raise ArchiveError("O destino da extração já existe.")
    dados_zip, _ = read_attachment_bytes(source, max_file_bytes=limits.max_zip_bytes)
    preparados, total, comprimido = _preparar_entradas(
        raiz, destino, dados_zip, limits
    )
    staging: Path | None = None
    try:
        staging = _criar_staging(raiz, limits.max_chars)
        _gravar_entradas(staging, preparados)
        _criar_pai(raiz, destino, limits.max_chars)
        staging.rename(destino)
    except OSError as exc:
        raise ArchiveError("A extração do ZIP não pôde ser concluída.") from exc
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    entradas = tuple(
        ArchiveEntry(
            path=preparado.classified.path,
            size=preparado.classified.size,
            sha256=preparado.classified.sha256,
            reasons=tuple(motivo.value for motivo in preparado.classified.reasons),
        )
        for preparado in preparados
    )
    return ArchiveReport(
        destination=destino.relative_to(raiz).as_posix(),
        entries=entradas,
        total_bytes=total,
        total_compressed=comprimido,
    )


def _validar_limites(limits: ArchiveLimits) -> None:
    """Rejeita limites que não podem proteger a extração."""
    obrigatorios = (limits.max_chars, limits.max_file_bytes, limits.max_total_bytes, limits.max_zip_bytes, limits.max_entries, limits.max_ratio)
    if any(valor < 1 for valor in obrigatorios) or limits.max_nesting < 0:
        raise ArchiveError("Os limites de extração são inválidos.")


def _raiz(root: Path) -> Path:
    """Confirma uma raiz real e sem ligações antes de qualquer escrita."""
    try:
        informacao = os.lstat(root)
    except OSError as exc:
        raise ArchiveError("A raiz do workspace não existe ou não pode ser lida.") from exc
    if _e_ligacao(root, informacao):
        raise ArchiveError("A raiz do workspace não pode ser uma ligação.")
    if not stat.S_ISDIR(informacao.st_mode):
        raise ArchiveError("A raiz do workspace tem de ser uma directoria.")
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ArchiveError("A raiz do workspace não pôde ser resolvida.") from exc


def _preparar_entradas(
    raiz: Path,
    destino: Path,
    dados_zip: bytes,
    limits: ArchiveLimits,
) -> tuple[list[_Preparado], int, int]:
    """Valida todas as entradas em memória antes de criar ficheiros."""
    try:
        with zipfile.ZipFile(io.BytesIO(dados_zip)) as arquivo:
            informacoes = arquivo.infolist()
            if len(informacoes) > limits.max_entries:
                raise ArchiveError("O ZIP excede o número de entradas permitido.")
            contexto = _Contexto(arquivo, raiz, destino, limits)
            preparados: list[_Preparado] = []
            total = 0
            comprimido = 0
            for informacao in informacoes:
                preparado, tamanho, compactado = _preparar_entrada(
                    contexto, informacao, total
                )
                if preparado is not None:
                    preparados.append(preparado)
                total += tamanho
                comprimido += compactado
            return preparados, total, comprimido
    except zipfile.BadZipFile as exc:
        raise ArchiveError("O ZIP é inválido ou está corrompido.") from exc
    except WorkspacePathError as exc:
        raise ArchiveError(str(exc)) from exc
    except (RuntimeError, NotImplementedError, EOFError, OSError) as exc:
        raise ArchiveError("Não foi possível ler uma entrada do ZIP.") from exc


def _preparar_entrada(
    contexto: _Contexto,
    informacao: zipfile.ZipInfo,
    total: int,
) -> tuple[_Preparado | None, int, int]:
    """Valida uma entrada e devolve os seus metadados sem a gravar."""
    limits = contexto.limits
    if _e_ligacao_zip(informacao):
        raise ArchiveError("O ZIP contém uma ligação e não pode ser extraído.")
    relativo = _relativo(
        contexto.raiz, contexto.destino, informacao.filename, limits.max_chars
    )
    if informacao.is_dir():
        return None, 0, informacao.compress_size
    tamanho = informacao.file_size
    if tamanho > limits.max_file_bytes:
        raise ArchiveError("Uma entrada do ZIP excede o limite de bytes por ficheiro.")
    if total + tamanho > limits.max_total_bytes:
        raise ArchiveError("O total descomprimido do ZIP excede o limite permitido.")
    if tamanho > max(1, informacao.compress_size) * limits.max_ratio:
        raise ArchiveError("O ZIP excede o rácio de compressão permitido.")
    dados = contexto.arquivo.read(informacao)
    if len(dados) != tamanho:
        raise ArchiveError("O tamanho declarado de uma entrada não corresponde aos dados.")
    nivel = sum(parte.lower().endswith(".zip") for parte in informacao.filename.replace("\\", "/").split("/")) + 1
    if nivel > limits.max_nesting and dados[:4] in _MAGICOS_ZIP:
        raise ArchiveError("O ZIP excede o nível de aninhamento permitido.")
    classificado = classify_bytes(
        dados,
        relative=relativo.relative_to(contexto.raiz).as_posix(),
        size=len(dados),
        max_file_bytes=limits.max_file_bytes,
    )
    return _Preparado(relativo.relative_to(contexto.destino), dados, classificado), tamanho, informacao.compress_size


def _relativo(raiz: Path, destino: Path, nome: str, max_chars: int) -> Path:
    """Converte o nome da entrada num caminho confinado ao destino."""
    if not nome.strip():
        raise ArchiveError("O ZIP contém uma entrada sem nome.")
    try:
        validate_workspace_path(raiz, nome, max_chars=max_chars)
    except WorkspacePathError as exc:
        raise ArchiveError(str(exc)) from exc
    relativo_destino = destino.relative_to(raiz).as_posix()
    candidato = f"{relativo_destino}/{nome.replace(chr(92), '/')}"
    try:
        caminho = validate_workspace_path(raiz, candidato, max_chars=max_chars)
    except WorkspacePathError as exc:
        raise ArchiveError(str(exc)) from exc
    if not caminho.is_relative_to(destino):
        raise ArchiveError("A entrada do ZIP sai da pasta de destino.")
    return caminho


def _e_ligacao_zip(informacao: zipfile.ZipInfo) -> bool:
    """Detecta ligações e tipos especiais declarados na entrada do ZIP."""
    modo = (informacao.external_attr >> 16) & _MODO_LIGACAO
    return modo in {
        stat.S_IFLNK,
        stat.S_IFBLK,
        stat.S_IFCHR,
        stat.S_IFIFO,
        stat.S_IFSOCK,
    }


def _criar_staging(raiz: Path, max_chars: int) -> Path:
    """Cria uma pasta temporária dentro da raiz para a extração."""
    candidato = f"{_STAGING}/{uuid.uuid4().hex}"
    try:
        caminho = validate_workspace_path(raiz, candidato, max_chars=max_chars)
        caminho.mkdir(parents=True)
    except WorkspacePathError as exc:
        raise ArchiveError(str(exc)) from exc
    return caminho


def _gravar_entradas(staging: Path, preparados: list[_Preparado]) -> None:
    """Grava as entradas já validadas na pasta temporária."""
    for preparado in preparados:
        alvo = staging / preparado.suffix
        alvo.parent.mkdir(parents=True, exist_ok=True)
        try:
            with alvo.open("xb") as ficheiro:
                ficheiro.write(preparado.data)
        except OSError as exc:
            raise ArchiveError("Não foi possível gravar a entrada do ZIP.") from exc


def _criar_pai(raiz: Path, destino: Path, max_chars: int) -> None:
    """Cria a cadeia de pastas de destino sem seguir ligações."""
    pai = destino.parent
    if pai == raiz:
        return
    acumulado: list[str] = []
    for parte in pai.relative_to(raiz).parts:
        acumulado.append(parte)
        try:
            candidato = validate_workspace_path(
                raiz, "/".join(acumulado), max_chars=max_chars
            )
        except WorkspacePathError as exc:
            raise ArchiveError(str(exc)) from exc
        if candidato.exists():
            informacao = os.lstat(candidato)
            if _e_ligacao(candidato, informacao) or not stat.S_ISDIR(informacao.st_mode):
                raise ArchiveError("A pasta de destino do ZIP não é segura.")
        else:
            candidato.mkdir()


def _e_ligacao(caminho: Path, informacao: os.stat_result) -> bool:
    """Detecta symlinks e junctions num caminho já inspecionado."""
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return caminho.is_symlink() or bool(atributos & reparse)
