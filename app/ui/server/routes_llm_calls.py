"""Consulta das chamadas LLM registadas pelo gateway."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs

from app.llm import ler_chamadas

LLM_CALLS_PATH = "/api/llm-calls"


def analisar_filtro_correlacao(consulta: str) -> str | None:
    """Lê um único correlation_id não vazio da consulta."""
    parametros = parse_qs(consulta, keep_blank_values=True)
    valores = parametros.get("correlation_id")
    if not valores:
        return None
    if len(valores) != 1 or not valores[0].strip():
        raise ValueError("correlation_id tem de ter um valor não vazio.")
    return valores[0]


def listar_chamadas(
    caminho: Path,
    correlation_id: str | None = None,
) -> list[dict[str, object]]:
    """Devolve chamadas ordenadas, opcionalmente filtradas por correlação."""
    return ler_chamadas(caminho, correlation_id)
