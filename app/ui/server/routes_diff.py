"""Cálculo verificável do diff do workspace para a aprovação local."""

from __future__ import annotations

from collections.abc import Sequence
from http import HTTPStatus
from typing import Final
from urllib.parse import parse_qs

from approvals.tokens import (
    ApprovalError,
    calcular_hash_diff,
    texto_obrigatorio,
)

from app.core.config import Settings
from app.workspace import (
    SnapshotError,
    SnapshotLimits,
    inventory_workspace,
    load_snapshot,
    snapshot_digest,
)

DIFF_PATH: Final = "/api/diff"
MAX_DIFF_FILES: Final = 100
_CAMPOS: Final = ("task_id", "correlation_id", "snapshot_id")


def analisar_consulta_diff(query: str) -> dict[str, str]:
    """Valida os parâmetros que ligam o diff à tarefa e à correlação."""
    consulta = parse_qs(query, keep_blank_values=True)
    extras = set(consulta) - set(_CAMPOS)
    if extras:
        raise ValueError("A consulta do diff contém parâmetros desconhecidos.")
    resultado: dict[str, str] = {}
    for nome in _CAMPOS:
        valores: Sequence[str] = consulta.get(nome, ())
        if len(valores) != 1:
            raise ValueError(f"O campo {nome} tem de aparecer uma única vez.")
        try:
            resultado[nome] = texto_obrigatorio(valores[0], nome)
        except ApprovalError as exc:
            raise ValueError(str(exc)) from exc
    return resultado


def calcular_diff_hash(snapshot_hash: object, alteracao_hash: object) -> str:
    """Devolve o digest canónico do diff a partir dos hashes verificados."""
    return calcular_hash_diff(snapshot_hash, alteracao_hash)


def processar_diff(settings: Settings, query: str) -> tuple[HTTPStatus, dict[str, object]]:
    """Prepara a resposta HTTP do diff sem expor excepções internas."""
    if not settings.diff:
        return HTTPStatus.NOT_FOUND, {"error": {"message": "Recurso não encontrado"}}
    try:
        resposta = calcular_diff(settings, analisar_consulta_diff(query))
    except ValueError as exc:
        return HTTPStatus.BAD_REQUEST, {"error": {"message": str(exc)}}
    return HTTPStatus.OK, resposta


def calcular_diff(settings: Settings, parametros: dict[str, str]) -> dict[str, object]:
    """Devolve o diff verificado entre o snapshot e o estado actual."""
    limites = _limites(settings)
    try:
        instantaneo = load_snapshot(
            settings.workspace_dir, parametros["snapshot_id"], limits=limites
        )
        entradas = inventory_workspace(settings.workspace_dir, limits=limites)
    except SnapshotError as exc:
        raise ValueError(str(exc)) from exc
    alteracao = snapshot_digest(entradas)
    try:
        diff = calcular_diff_hash(instantaneo.digest, alteracao)
    except ApprovalError as exc:
        raise ValueError("Os hashes do workspace não são verificáveis.") from exc
    return {
        "task_id": parametros["task_id"],
        "correlation_id": parametros["correlation_id"],
        "snapshot_id": parametros["snapshot_id"],
        "snapshot_hash": instantaneo.digest,
        "alteracao_hash": alteracao,
        "diff_hash": diff,
    }


def _limites(settings: Settings) -> SnapshotLimits:
    """Deriva limites seguros para a leitura do workspace."""
    return SnapshotLimits(
        max_chars=settings.max_workspace_path_chars,
        max_file_bytes=settings.max_workspace_file_bytes,
        max_total_bytes=settings.max_workspace_file_bytes * MAX_DIFF_FILES,
        max_files=MAX_DIFF_FILES,
    )
