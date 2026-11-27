"""Snapshots verificáveis do workspace."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path

_SNAPSHOTS = ".snapshots"
_STAGING = ".snapshot-staging"
_MANIFEST = "manifest.json"
_INTERNOS = frozenset(
    {
        ".archive-staging",
        ".quarantine",
        ".rollback-staging",
        ".snapshot-staging",
        ".snapshots",
    }
)
_TAMANHO_BLOCO = 65_536


class SnapshotError(ValueError):
    """Snapshot inválido, incompleto ou que não pôde ser criado."""


@dataclass(frozen=True)
class SnapshotLimits:
    """Limites aplicados ao inventário e à cópia do snapshot."""

    max_chars: int
    max_file_bytes: int
    max_total_bytes: int
    max_files: int


@dataclass(frozen=True)
class SnapshotEntry:
    """Metadados verificáveis de um ficheiro do workspace."""

    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class Snapshot:
    """Snapshot confirmado, com o digest do seu manifesto."""

    id: str
    digest: str
    entries: tuple[SnapshotEntry, ...]
    total_bytes: int


def snapshot_digest(entries: Sequence[SnapshotEntry]) -> str:
    """Calcula o digest canónico de um inventário de ficheiros."""
    serializado = json.dumps(
        [
            {"path": item.path, "size": item.size, "sha256": item.sha256}
            for item in entries
        ],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def inventory_workspace(root: Path, *, limits: SnapshotLimits) -> tuple[SnapshotEntry, ...]:
    """Lista e hashed todos os ficheiros normais do workspace."""
    _validar_limites(limits)
    raiz = _validar_raiz(root)
    entradas: list[SnapshotEntry] = []
    total = 0

    def falhar(erro: OSError) -> None:
        """Transforma erros de percurso em erro de snapshot."""
        raise SnapshotError("Não foi possível percorrer o workspace.") from erro

    for atual, nomes_dir, nomes_ficheiro in os.walk(raiz, onerror=falhar):
        nomes_dir[:] = sorted(
            nome
            for nome in nomes_dir
            if nome not in _INTERNOS and _diretorio_seguro(Path(atual) / nome)
        )
        for nome in sorted(nomes_ficheiro):
            relativo = _relativo(raiz, Path(atual) / nome)
            if relativo.split("/", 1)[0] in _INTERNOS:
                continue
            if len(entradas) >= limits.max_files:
                raise SnapshotError("O workspace excede o número de ficheiros permitido.")
            caminho = validate_workspace_path(
                raiz, relativo, max_chars=limits.max_chars
            )
            informacao = os.lstat(caminho)
            if _e_ligacao(caminho, informacao) or not stat.S_ISREG(informacao.st_mode):
                raise SnapshotError("O workspace contém uma ligação ou ficheiro especial.")
            if informacao.st_size > limits.max_file_bytes:
                raise SnapshotError("Um ficheiro excede o limite de bytes do snapshot.")
            digest, tamanho = _digest_ficheiro(caminho, limits.max_file_bytes)
            total += tamanho
            if total > limits.max_total_bytes:
                raise SnapshotError("O workspace excede o total de bytes permitido.")
            entradas.append(SnapshotEntry(relativo, tamanho, digest))
    return tuple(entradas)


def create_snapshot(root: Path, *, limits: SnapshotLimits) -> Snapshot:
    """Cria um snapshot atómico do estado actual do workspace."""
    entradas = inventory_workspace(root, limits=limits)
    raiz = _validar_raiz(root)
    ident = uuid.uuid4().hex
    digest = snapshot_digest(entradas)
    staging = _criar_staging(raiz, limits)
    try:
        _copiar_para_staging(raiz, staging, entradas, limits)
        _gravar_manifest(staging, ident, digest, entradas)
        destino = _destino_snapshot(raiz, ident, limits)
        staging.rename(destino)
    except (OSError, WorkspacePathError) as exc:
        raise SnapshotError("O snapshot não pôde ser gravado.") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        try:
            staging.parent.rmdir()
        except OSError:
            pass
    return Snapshot(ident, digest, entradas, sum(item.size for item in entradas))


def _validar_limites(limits: SnapshotLimits) -> None:
    """Rejeita limites que não podem proteger o snapshot."""
    valores = [
        limits.max_chars, limits.max_file_bytes,
        limits.max_total_bytes, limits.max_files,
    ]
    if any(valor < 1 for valor in valores):
        raise SnapshotError("Os limites do snapshot são inválidos.")


def _validar_raiz(root: Path) -> Path:
    """Confirma uma raiz real e sem ligações antes de qualquer acesso."""
    try:
        informacao = os.lstat(root)
    except OSError as exc:
        raise SnapshotError("A raiz do workspace não existe ou não pode ser lida.") from exc
    if _e_ligacao(root, informacao):
        raise SnapshotError("A raiz do workspace não pode ser uma ligação.")
    if not stat.S_ISDIR(informacao.st_mode):
        raise SnapshotError("A raiz do workspace tem de ser uma directoria.")
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SnapshotError("A raiz do workspace não pôde ser resolvida.") from exc


def _e_ligacao(caminho: Path, informacao: os.stat_result) -> bool:
    """Detecta symlinks e junctions sem seguir o destino."""
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return caminho.is_symlink() or bool(atributos & reparse)


def _diretorio_seguro(caminho: Path) -> bool:
    """Indica se uma diretória pode ser percorrida com segurança."""
    try:
        informacao = os.lstat(caminho)
    except OSError:
        return False
    return not _e_ligacao(caminho, informacao) and stat.S_ISDIR(informacao.st_mode)


def _relativo(raiz: Path, caminho: Path) -> str:
    """Devolve o caminho relativo normalizado com separadores '/'."""
    try:
        return caminho.relative_to(raiz).as_posix()
    except ValueError as exc:
        raise SnapshotError("O ficheiro sai da raiz do workspace.") from exc


def _digest_ficheiro(caminho: Path, max_file_bytes: int) -> tuple[str, int]:
    """Lê um ficheiro em blocos e devolve o SHA-256 e o tamanho."""
    digest = hashlib.sha256()
    tamanho = 0
    try:
        with caminho.open("rb") as ficheiro:
            while bloco := ficheiro.read(_TAMANHO_BLOCO):
                tamanho += len(bloco)
                if tamanho > max_file_bytes:
                    raise SnapshotError("Um ficheiro excede o limite de bytes do snapshot.")
                digest.update(bloco)
    except OSError as exc:
        raise SnapshotError("Não foi possível ler um ficheiro do workspace.") from exc
    return digest.hexdigest(), tamanho


def _criar_staging(raiz: Path, limits: SnapshotLimits) -> Path:
    """Cria uma pasta temporária dentro da raiz para o snapshot."""
    candidato = f"{_STAGING}/{uuid.uuid4().hex}"
    try:
        caminho = validate_workspace_path(
            raiz, candidato, max_chars=limits.max_chars
        )
        caminho.mkdir(parents=True)
    except (OSError, WorkspacePathError) as exc:
        raise SnapshotError("Não foi possível preparar o staging do snapshot.") from exc
    return caminho


def _copiar_para_staging(
    raiz: Path,
    staging: Path,
    entradas: tuple[SnapshotEntry, ...],
    limits: SnapshotLimits,
) -> None:
    """Copia os ficheiros já inventariados para o staging."""
    for entrada in entradas:
        origem = validate_workspace_path(
            raiz, entrada.path, max_chars=limits.max_chars
        )
        destino = validate_workspace_path(
            staging, entrada.path, max_chars=limits.max_chars
        )
        destino.parent.mkdir(parents=True, exist_ok=True)
        digest, tamanho = _copiar_e_hash(origem, destino, limits.max_file_bytes)
        if digest != entrada.sha256 or tamanho != entrada.size:
            raise SnapshotError("Um ficheiro mudou durante a cópia do snapshot.")


def _copiar_e_hash(origem: Path, destino: Path, max_file_bytes: int) -> tuple[str, int]:
    """Copia um ficheiro uma vez e devolve o hash copiado."""
    digest = hashlib.sha256()
    tamanho = 0
    try:
        with origem.open("rb") as leitura, destino.open("xb") as escrita:
            while bloco := leitura.read(_TAMANHO_BLOCO):
                tamanho += len(bloco)
                if tamanho > max_file_bytes:
                    raise SnapshotError("Um ficheiro excede o limite de bytes do snapshot.")
                escrita.write(bloco)
                digest.update(bloco)
    except OSError as exc:
        raise SnapshotError("Não foi possível copiar um ficheiro para o snapshot.") from exc
    return digest.hexdigest(), tamanho


def _gravar_manifest(
    staging: Path,
    ident: str,
    digest: str,
    entradas: tuple[SnapshotEntry, ...],
) -> None:
    """Grava apenas metadados verificáveis do snapshot."""
    conteudo = {
        "id": ident,
        "digest": digest,
        "entries": [
            {"path": item.path, "size": item.size, "sha256": item.sha256}
            for item in entradas
        ],
    }
    try:
        with (staging / _MANIFEST).open("x", encoding="utf-8") as ficheiro:
            json.dump(conteudo, ficheiro, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        raise SnapshotError("Não foi possível gravar o manifesto do snapshot.") from exc


def _destino_snapshot(
    raiz: Path, ident: str, limits: SnapshotLimits
) -> Path:
    """Prepara a pasta final do snapshot sem seguir ligações."""
    base = raiz / _SNAPSHOTS
    try:
        if base.exists():
            informacao = os.lstat(base)
            if _e_ligacao(base, informacao) or not stat.S_ISDIR(informacao.st_mode):
                raise SnapshotError("A pasta de snapshots não é segura.")
        else:
            base.mkdir()
        destino = validate_workspace_path(
            raiz, f"{_SNAPSHOTS}/{ident}", max_chars=limits.max_chars
        )
    except (OSError, WorkspacePathError) as exc:
        raise SnapshotError("Não foi possível preparar a pasta do snapshot.") from exc
    if destino.exists():
        raise SnapshotError("O identificador do snapshot já existe.")
    return destino
