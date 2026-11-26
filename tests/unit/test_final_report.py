"""Testes do gerador seguro do relatório final."""

from __future__ import annotations

from reports.final_report import renderizar_relatorio
from tests.eval.scorer import CaseResult, ResultadoAvaliacao, Verificacao


def test_relatorio_preserva_nomes_das_verificacoes() -> None:
    """Nomes descritivos não são confundidos com valores sensíveis."""
    avaliacao = ResultadoAvaliacao(
        (
            CaseResult(
                "golden_calculadora",
                (Verificacao("token de outra tarefa recusado", True),),
            ),
        ),
        minimo=1,
    )
    texto = renderizar_relatorio(avaliacao)
    assert "| golden_calculadora | token de outra tarefa recusado | PASSA |" in texto


def test_relatorio_filtra_valores_sensiveis_e_digests_invalidos() -> None:
    """Apenas digests válidos e valores curtos chegam ao relatório."""
    avaliacao = ResultadoAvaliacao(
        (
            CaseResult(
                "golden_calculadora", (Verificacao("fluxo ponta a ponta", True),)
            ),
        ),
        minimo=1,
    )
    texto = renderizar_relatorio(
        avaliacao,
        resultados={"segredo": "valor-sensivel-123", "ruff": "0 errors"},
        evidencias={"diff_hash": "a" * 64, "token_hash": "token-real-curto"},
    )
    assert "valor-sensivel-123" not in texto
    assert "token-real-curto" not in texto
    assert "0 errors" in texto
    assert "`" + "a" * 64 + "`" in texto
