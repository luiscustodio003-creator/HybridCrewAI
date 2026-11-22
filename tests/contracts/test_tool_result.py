"""Contratos dos resultados de ferramentas verificados."""

from __future__ import annotations

import pytest

from app.core.results import (
    ToolResult,
    ToolResultError,
    ToolStatus,
    new_tool_result,
    validar_tool_result,
)


@pytest.mark.parametrize(
    ("estado", "extra"),
    [
        (ToolStatus.DONE, {"evidence": ("relatorio.pdf",)}),
        (ToolStatus.UNVERIFIED, {}),
        (ToolStatus.FAILED, {"error": "comando falhou"}),
        (ToolStatus.ASK, {"question": "Qual ficheiro?"}),
        (ToolStatus.STARTED, {}),
    ],
)
def test_cinco_estados_sao_aceites(
    estado: ToolStatus, extra: dict[str, object]
) -> None:
    """Os cinco estados do contrato são construíveis."""
    resultado = new_tool_result(status=estado, summary="Resumo", **extra)
    assert resultado.status is estado
    assert resultado.summary == "Resumo"
    validar_tool_result(resultado)


def test_done_sem_evidencia_e_rejeitado() -> None:
    """Um resultado concluído sem prova não é aceite."""
    with pytest.raises(ToolResultError, match="done requer evidencia"):
        new_tool_result(status=ToolStatus.DONE, summary="Resumo")


def test_done_com_evidencia_vazia_e_rejeitado() -> None:
    """Entradas de evidência vazias não contam como prova."""
    with pytest.raises(ToolResultError, match="evidencia nao pode ser vazia"):
        new_tool_result(
            status=ToolStatus.DONE, summary="Resumo", evidence=("",)
        )


def test_estados_invalidos_sao_rejeitados() -> None:
    """O esquema aceita apenas os valores minúsculos declarados."""
    with pytest.raises(ValueError):
        new_tool_result(status="DONE", summary="Resumo")


def test_resultado_e_imutavel() -> None:
    """O contrato é imutável por desenho."""
    resultado = ToolResult(status=ToolStatus.STARTED, summary="Resumo")
    with pytest.raises(AttributeError):
        resultado.summary = "Outro"  # type: ignore[misc]


def test_regras_de_estado_sao_verificadas() -> None:
    """Cada estado exige os seus campos e rejeita campos incoerentes."""
    with pytest.raises(ToolResultError, match="failed requer error"):
        new_tool_result(status=ToolStatus.FAILED, summary="Resumo")
    with pytest.raises(ToolResultError, match="ask requer question"):
        new_tool_result(status=ToolStatus.ASK, summary="Resumo")
    with pytest.raises(ToolResultError, match="started nao aceita error"):
        new_tool_result(
            status=ToolStatus.STARTED, summary="Resumo", error="erro"
        )
    with pytest.raises(ToolResultError, match="done nao aceita question"):
        new_tool_result(
            status=ToolStatus.DONE,
            summary="Resumo",
            evidence=("evidencia",),
            question="Qual?",
        )
