"""Rollback e undo de snapshots verificáveis do workspace."""

from __future__ import annotations

import hmac
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.snapshot import (
    _MANIFEST,
    Snapshot,
    SnapshotEntry,
    SnapshotError,
    SnapshotLimits,
    _copiar_e_hash,
    _digest_ficheiro,
    _validar_limites,
    _validar_raiz,
    create_snapshot,
    inventory_workspace,
    snapshot_digest,
)

_ID_PADRAO = re.compile(r"^[0-9a-f]{32}$")
_HASH_PADRAO = re.compile(r"^[0-9a-f]{64}$")
_STAGING = ".rollback-staging"


class RollbackError(ValueError):
    """Rollback ou undo recusado, interrompido ou não verificado."""


@dataclass(frozen=True)
class RollbackReport:
    """Resultado verificado de um rollback."""

    snapshot_id: str
    undo_id: str
    restored_digest: str
    entries: tuple[SnapshotEntry, ...]


@dataclass(frozen=True)
class UndoReport:
    """Resultado verificado de um undo."""

    undo_id: str
    restored_digest: str
    entries: tuple[SnapshotEntry, ...]


def load_snapshot(root: Path, snapshot_id: str, *, limits: SnapshotLimits) -> Snapshot:
    """Lê um snapshot e verifica todos os ficheiros e o manifesto."""
    _validar_limites(limits)
    if not _ID_PADRAO.fullmatch(snapshot_id):
        raise SnapshotError("O identificador do snapshot é inválido.")
    raiz = _validar_raiz(root)
    diretorio = validate_workspace_path(
        raiz, f".snapshots/{snapshot_id}", max_chars=limits.max_chars
    )
    manifesto = _ler_manifest(diretorio, limits)
    entradas = _entradas_do_manifest(manifesto.get("entries"), limits)
    digest = snapshot_digest(entradas)
    if manifesto.get("id") != snapshot_id or not hmac.compare_digest(
        str(manifesto.get("digest", "")), digest
    ):
        raise SnapshotError("O manifesto do snapshot não corresponde ao identificador.")
    for entrada in entradas:
        caminho = validate_workspace_path(
            diretorio, entrada.path, max_chars=limits.max_chars
        )
        real, tamanho = _digest_ficheiro(caminho, limits.max_file_bytes)
        if real != entrada.sha256 or tamanho != entrada.size:
            raise SnapshotError("Um ficheiro do snapshot falhou a verificação de hash.")
    return Snapshot(snapshot_id, digest, entradas, sum(item.size for item in entradas))


def rollback(root: Path, snapshot_id: str, *, limits: SnapshotLimits) -> RollbackReport:
    """Restaura um snapshot depois de guardar o estado actual como undo."""
    _validar_limites(limits)
    if not _ID_PADRAO.fullmatch(snapshot_id):
        raise RollbackError("O identificador do snapshot é inválido.")
    _validar_raiz(root)
    try:
        instantaneo = load_snapshot(root, snapshot_id, limits=limits)
    except SnapshotError as exc:
        raise RollbackError("O snapshot não pôde ser verificado.") from exc
    undo = create_snapshot(root, limits=limits)
    final = _aplicar(root, instantaneo, limits)
    return RollbackReport(snapshot_id, undo.id, instantaneo.digest, final)


def undo_rollback(root: Path, undo_id: str, *, limits: SnapshotLimits) -> UndoReport:
    """Desfaz um rollback usando o snapshot do estado pós-alteração."""
    _validar_limites(limits)
    if not _ID_PADRAO.fullmatch(undo_id):
        raise RollbackError("O identificador do undo é inválido.")
    _validar_raiz(root)
    try:
        instantaneo = load_snapshot(root, undo_id, limits=limits)
    except SnapshotError as exc:
        raise RollbackError("O undo não pôde ser verificado.") from exc
    final = _aplicar(root, instantaneo, limits)
    return UndoReport(undo_id, instantaneo.digest, final)


def _substituir(origem: Path, destino: Path) -> None:
    """Substitui um ficheiro por outro sem copiar conteúdo extra."""
    os.replace(origem, destino)


def _aplicar(
    root: Path, instantaneo: Snapshot, limits: SnapshotLimits
) -> tuple[SnapshotEntry, ...]:
    """Copia um snapshot verificado para o workspace e confirma o resultado."""
    raiz = _validar_raiz(root)
    staging = _criar_staging(raiz, limits)
    destinos = {entrada.path for entrada in instantaneo.entries}
    try:
        _copiar_snapshot(raiz, staging, instantaneo, limits)
        atual = inventory_workspace(raiz, limits=limits)
        removiveis = [item.path for item in atual if item.path not in destinos]
        for relativo in sorted(destinos):
            origem = validate_workspace_path(
                staging, relativo, max_chars=limits.max_chars
            )
            destino = validate_workspace_path(
                raiz, relativo, max_chars=limits.max_chars
            )
            destino.parent.mkdir(parents=True, exist_ok=True)
            _substituir(origem, destino)
        for relativo in sorted(removiveis):
            caminho = validate_workspace_path(
                raiz, relativo, max_chars=limits.max_chars
            )
            if caminho.exists():
                caminho.unlink()
        final = inventory_workspace(raiz, limits=limits)
        digest_final = snapshot_digest(final)
        if not hmac.compare_digest(digest_final, instantaneo.digest):
            raise RollbackError("O estado final não corresponde ao snapshot.")
    except (OSError, WorkspacePathError, SnapshotError, RollbackError) as exc:
        raise RollbackError("O snapshot não pôde ser aplicado.") from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        try:
            staging.parent.rmdir()
        except OSError:
            pass
    return final


def _criar_staging(raiz: Path, limits: SnapshotLimits) -> Path:
    """Cria uma pasta temporária para aplicar o snapshot."""
    candidato = f"{_STAGING}/{uuid.uuid4().hex}"
    try:
        caminho = validate_workspace_path(
            raiz, candidato, max_chars=limits.max_chars
        )
        caminho.mkdir(parents=True)
    except (OSError, WorkspacePathError) as exc:
        raise RollbackError("Não foi possível preparar o staging do rollback.") from exc
    return caminho


def _copiar_snapshot(
    raiz: Path,
    staging: Path,
    instantaneo: Snapshot,
    limits: SnapshotLimits,
) -> None:
    """Copia o snapshot verificado para o staging do rollback."""
    origem_raiz = validate_workspace_path(
        raiz, f".snapshots/{instantaneo.id}", max_chars=limits.max_chars
    )
    for entrada in instantaneo.entries:
        origem = validate_workspace_path(
            origem_raiz, entrada.path, max_chars=limits.max_chars
        )
        destino = validate_workspace_path(
            staging, entrada.path, max_chars=limits.max_chars
        )
        destino.parent.mkdir(parents=True, exist_ok=True)
        digest, tamanho = _copiar_e_hash(origem, destino, limits.max_file_bytes)
        if digest != entrada.sha256 or tamanho != entrada.size:
            raise RollbackError("Um ficheiro do snapshot mudou durante o rollback.")


def _ler_manifest(diretorio: Path, limits: SnapshotLimits) -> dict[str, object]:
    """Lê e valida a estrutura básica do manifesto."""
    caminho = validate_workspace_path(
        diretorio, _MANIFEST, max_chars=limits.max_chars
    )
    try:
        if caminho.stat().st_size > limits.max_files * 512:
            raise SnapshotError("O manifesto do snapshot é demasiado grande.")
        with caminho.open("r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)
    except (OSError, ValueError) as exc:
        raise SnapshotError("O manifesto do snapshot não pôde ser lido.") from exc
    if not isinstance(dados, dict):
        raise SnapshotError("O manifesto do snapshot está inválido.")
    return dados


def _entradas_do_manifest(
    valor: object, limits: SnapshotLimits
) -> tuple[SnapshotEntry, ...]:
    """Converte as entradas do manifesto em objetos verificáveis."""
    if not isinstance(valor, list) or len(valor) > limits.max_files:
        raise SnapshotError("O inventário do snapshot está incompleto.")
    entradas: list[SnapshotEntry] = []
    total = 0
    for bruto in valor:
        if not isinstance(bruto, dict):
            raise SnapshotError("O inventário do snapshot está inválido.")
        caminho = bruto.get("path")
        tamanho = bruto.get("size")
        digest = bruto.get("sha256")
        if not isinstance(caminho, str) or not caminho.strip():
            raise SnapshotError("O inventário do snapshot tem um caminho inválido.")
        if (
            isinstance(tamanho, bool)
            or not isinstance(tamanho, int)
            or not 0 <= tamanho <= limits.max_file_bytes
        ):
            raise SnapshotError("O inventário do snapshot tem um tamanho inválido.")
        if not isinstance(digest, str) or not _HASH_PADRAO.fullmatch(digest):
            raise SnapshotError("O inventário do snapshot tem um hash inválido.")
        total += tamanho
        if total > limits.max_total_bytes:
            raise SnapshotError("O inventário do snapshot excede o total permitido.")
        entradas.append(SnapshotEntry(caminho, tamanho, digest))
    return tuple(entradas)
