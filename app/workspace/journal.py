"""Journal e tipos das operações atómicas de ficheiro."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.snapshot import SnapshotLimits, inventory_workspace, snapshot_digest

DIRETORIO = ".file-ops"
STAGING = "staging"
PENDING = "journal/pending"
COMMITTED = "journal/committed"
_ID_PADRAO = re.compile(r"^[0-9a-f]{32}$")
_HASH_PADRAO = re.compile(r"^[0-9a-f]{64}$")
_INTERNOS = frozenset({".file-ops", ".snapshots", ".archive-staging", ".quarantine"})


class FileOpsError(RuntimeError):
    """Escrita rejeitada, interrompida ou que não pôde ser recuperada."""


@dataclass(frozen=True)
class FileOpLimits:
    """Limites aplicados a uma operação de escrita no workspace."""

    max_chars: int
    max_file_bytes: int
    max_total_bytes: int
    max_files: int


@dataclass(frozen=True)
class FileChange:
    """Conteúdo a gravar num caminho relativo do workspace."""

    path: str
    data: bytes


@dataclass(frozen=True)
class FileOpReport:
    """Resultado de uma operação confirmada e aplicada."""

    operation_id: str
    digest: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryReport:
    """Resultado da recuperação de operações pendentes."""

    operation_ids: tuple[str, ...]
    restored_files: int
    discarded: int


def validar_limites(limits: FileOpLimits) -> None:
    """Rejeita limites que não protegem a operação."""
    valores = (
        limits.max_chars,
        limits.max_file_bytes,
        limits.max_total_bytes,
        limits.max_files,
    )
    if any(valor < 1 for valor in valores):
        raise FileOpsError("Os limites da operação são inválidos.")


def raiz_segura(root: Path) -> Path:
    """Confirma uma raiz real, directória e sem ligações."""
    try:
        informacao = os.lstat(root)
        if root.is_symlink() or not stat.S_ISDIR(informacao.st_mode):
            raise FileOpsError("A raiz do workspace não é uma directória segura.")
        return root.resolve(strict=True)
    except OSError as exc:
        raise FileOpsError("A raiz do workspace não existe ou não pode ser lida.") from exc


def caminho_interno(raiz: Path, relativo: str, limits: FileOpLimits) -> Path:
    """Valida um caminho interno antes de o usar."""
    try:
        return validate_workspace_path(raiz, relativo, max_chars=limits.max_chars)
    except WorkspacePathError as exc:
        raise FileOpsError("O caminho interno da operação é inválido.") from exc


def eh_interno(relativo: str) -> bool:
    """Indica se o caminho pertence a uma directória reservada."""
    return relativo.split("/", 1)[0] in _INTERNOS


def novo_manifest(
    raiz: Path,
    operacao: str,
    previstos: Sequence[Mapping[str, object]],
    limits: FileOpLimits,
) -> dict[str, object]:
    """Cria o manifesto canónico da operação."""
    entradas = [
        {"path": item["path"], "size": item["size"], "sha256": item["sha256"]}
        for item in previstos
    ]
    return {
        "operation_id": operacao,
        "base_digest": _digest_atual(raiz, limits),
        "digest": calcular_digest(entradas),
        "files": entradas,
    }


def calcular_digest(entradas: Sequence[Mapping[str, object]]) -> str:
    """Calcula o digest canónico de uma lista de entradas."""
    serializado = json.dumps(
        list(entradas), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def preparar_staging(
    raiz: Path, operacao: str, limits: FileOpLimits
) -> Path:
    """Cria a pasta de staging da operação dentro da raiz."""
    caminho = caminho_interno(
        raiz, f"{DIRETORIO}/{STAGING}/{operacao}", limits
    )
    try:
        caminho.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise FileOpsError("O staging da operação já existe.") from exc
    return caminho


def gravar_json(
    destino: Path, dados: Mapping[str, object], raiz: Path, limits: FileOpLimits
) -> None:
    """Grava um manifesto por substituição atómica."""
    relativo = f"{DIRETORIO}/{PENDING}/{destino.stem}.{os.urandom(16).hex()}.tmp"
    temporario = caminho_interno(raiz, relativo, limits)
    conteudo = json.dumps(dados, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with temporario.open("x", encoding="utf-8") as ficheiro:
            ficheiro.write(conteudo)
        os.replace(temporario, destino)
    except OSError as exc:
        raise FileOpsError("O manifesto da operação não pôde ser gravado.") from exc
    finally:
        temporario.unlink(missing_ok=True)


def listar_manifestos(
    raiz: Path, seccao: str, limits: FileOpLimits
) -> list[tuple[Path, dict[str, object]]]:
    """Lista manifestos válidos de uma secção do journal."""
    diretorio = caminho_interno(raiz, f"{DIRETORIO}/{seccao}", limits)
    if not diretorio.exists():
        return []
    manifestos: list[tuple[Path, dict[str, object]]] = []
    for candidato in sorted(diretorio.glob("*.json")):
        if not _ID_PADRAO.fullmatch(candidato.stem):
            raise FileOpsError("O journal contém um identificador inválido.")
        try:
            dados = json.loads(candidato.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise FileOpsError("O manifesto do journal não pôde ser lido.") from exc
        if not isinstance(dados, dict):
            raise FileOpsError("O manifesto do journal está inválido.")
        validar_manifest(dados, limits)
        manifestos.append((candidato, dados))
    return manifestos


def validar_manifest(dados: Mapping[str, object], limits: FileOpLimits) -> None:
    """Valida a estrutura e os hashes de um manifesto recuperado."""
    operacao = dados.get("operation_id")
    if not isinstance(operacao, str) or not _ID_PADRAO.fullmatch(operacao):
        raise FileOpsError("A operação do manifesto é inválida.")
    for chave in ("base_digest", "digest"):
        valor = dados.get(chave)
        if not isinstance(valor, str) or not _HASH_PADRAO.fullmatch(valor):
            raise FileOpsError("O digest do manifesto é inválido.")
    entradas = dados.get("files")
    if not isinstance(entradas, list) or not 1 <= len(entradas) <= limits.max_files:
        raise FileOpsError("As entradas do manifesto são inválidas.")
    total = 0
    for bruto in entradas:
        item = entrada(bruto)
        total += int(str(item["size"]))
    if total > limits.max_total_bytes:
        raise FileOpsError("O manifesto excede o total de bytes permitido.")
    if not isinstance(dados["digest"], str) or dados["digest"] != calcular_digest(entradas):
        raise FileOpsError("O digest do manifesto não corresponde às entradas.")


def entrada(valor: object) -> dict[str, object]:
    """Converte uma entrada do manifesto em metadados verificáveis."""
    if not isinstance(valor, dict):
        raise FileOpsError("A entrada do manifesto não é um objecto.")
    caminho = valor.get("path")
    tamanho = valor.get("size")
    digest = valor.get("sha256")
    if not isinstance(caminho, str) or not caminho.strip():
        raise FileOpsError("A entrada do manifesto tem um caminho inválido.")
    if isinstance(tamanho, bool) or not isinstance(tamanho, int) or tamanho < 0:
        raise FileOpsError("A entrada do manifesto tem um tamanho inválido.")
    if not isinstance(digest, str) or not _HASH_PADRAO.fullmatch(digest):
        raise FileOpsError("A entrada do manifesto tem um hash inválido.")
    return {"path": caminho, "size": tamanho, "sha256": digest}


def digest_arquivo(caminho: Path, max_bytes: int) -> tuple[str, int]:
    """Lê um ficheiro em blocos e devolve o SHA-256 e o tamanho."""
    digest = hashlib.sha256()
    tamanho = 0
    try:
        with caminho.open("rb") as ficheiro:
            while bloco := ficheiro.read(65_536):
                tamanho += len(bloco)
                if tamanho > max_bytes:
                    raise FileOpsError("O ficheiro excede o limite de bytes da operação.")
                digest.update(bloco)
    except OSError as exc:
        raise FileOpsError("O ficheiro não pôde ser lido.") from exc
    return digest.hexdigest(), tamanho


def limpar_operacao(
    raiz: Path, operacao: str, limits: FileOpLimits
) -> None:
    """Remove journal e staging de uma operação concluída ou abortada."""
    for seccao in (PENDING, COMMITTED):
        caminho = caminho_interno(
            raiz, f"{DIRETORIO}/{seccao}/{operacao}.json", limits
        )
        caminho.unlink(missing_ok=True)
    remover_staging(caminho_interno(
        raiz, f"{DIRETORIO}/{STAGING}/{operacao}", limits
    ))


def remover_staging(staging: Path) -> None:
    """Remove uma directória de staging sem seguir ligações externas."""
    if staging.is_symlink():
        staging.unlink()
        return
    shutil.rmtree(staging, ignore_errors=True)


def limpar_orfos(
    raiz: Path,
    confirmados: Sequence[tuple[Path, dict[str, object]]],
    pendentes: Sequence[tuple[Path, dict[str, object]]],
    limits: FileOpLimits,
) -> int:
    """Descarta staging sem manifesto e devolve o número removido."""
    diretorio = caminho_interno(raiz, f"{DIRETORIO}/{STAGING}", limits)
    if not diretorio.exists() or diretorio.is_symlink():
        return 0
    conhecidos = {
        str(manifesto["operation_id"])
        for _, manifesto in (*confirmados, *pendentes)
    }
    removidos = 0
    for filho in diretorio.iterdir():
        if filho.name not in conhecidos:
            remover_staging(filho)
            removidos += 1
    return removidos


def _digest_atual(raiz: Path, limits: FileOpLimits) -> str:
    """Calcula o digest do estado actual do workspace."""
    inventario = inventory_workspace(
        raiz,
        limits=SnapshotLimits(
            max_chars=limits.max_chars,
            max_file_bytes=limits.max_file_bytes,
            max_total_bytes=limits.max_total_bytes,
            max_files=limits.max_files,
        ),
    )
    return snapshot_digest(inventario)
