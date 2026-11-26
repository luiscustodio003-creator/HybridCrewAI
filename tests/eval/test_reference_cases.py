"""Testes do harness de avaliação com cinco casos de referência."""

from __future__ import annotations

from pathlib import Path

import pytest
from reports.final_report import renderizar_relatorio
from tests.eval.cases import CASES, CASO_DOURADO_ID
from tests.eval.scorer import (
    LIMITE_INFERIOR,
    MINIMO_APROVACAO,
    TAMANHO_DIGEST,
    TOTAL_CASOS,
    Case,
    CaseResult,
    Verificacao,
    digest_casos,
    executar_caso,
    pontuar,
)


def _executar_todos(tmp_path: Path) -> tuple[CaseResult, ...]:
    resultados: list[CaseResult] = []
    for caso in CASES:
        destino = tmp_path / caso.id
        destino.mkdir()
        patches = pytest.MonkeyPatch()
        try:
            resultados.append(executar_caso(caso, destino, patches))
        finally:
            patches.undo()
    return tuple(resultados)


@pytest.mark.parametrize("caso", CASES, ids=lambda caso: caso.id)
def test_caso_de_referencia(
    caso: Case, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resultado = executar_caso(caso, tmp_path, monkeypatch)
    for verificacao in resultado.verificacoes:
        assert verificacao.passou, (
            f"{caso.id}: {verificacao.nome} — {verificacao.detalhe}"
        )


def test_cinco_casos_pontuacao_minima_e_dourado_obrigatorio(tmp_path: Path) -> None:
    resultados = _executar_todos(tmp_path)
    falhas = [item.case_id for item in resultados if not item.aprovado]
    assert not falhas, falhas
    avaliacao = pontuar(resultados)
    assert avaliacao.total == TOTAL_CASOS
    assert avaliacao.pontuacao >= MINIMO_APROVACAO
    assert avaliacao.caso_dourado_presente
    assert avaliacao.aprovado
    assert len(digest_casos(avaliacao)) == TAMANHO_DIGEST
    sem_dourado = pontuar(
        tuple(item for item in resultados if item.case_id != CASO_DOURADO_ID)
    )
    assert sem_dourado.pontuacao == MINIMO_APROVACAO
    assert sem_dourado.aprovado is False


def test_pontuacao_inferior_ao_minimo_nao_aprova() -> None:
    resultados = tuple(
        CaseResult(
            f"caso-{indice}",
            (Verificacao("verificação", indice < LIMITE_INFERIOR),),
        )
        for indice in range(TOTAL_CASOS)
    )
    avaliacao = pontuar(resultados)
    assert avaliacao.pontuacao == LIMITE_INFERIOR
    assert avaliacao.aprovado is False


def test_relatorio_nao_expoe_token_nem_prompt() -> None:
    avaliacao = pontuar(
        (CaseResult("caso-teste", (Verificacao("verificação", True),)),),
        minimo=1,
    )
    segredo = "token-falso-relatorio-123456"
    prompt = "prompt completo que nao deve aparecer"
    texto = renderizar_relatorio(
        avaliacao,
        comandos=["python -m pytest -q tests/eval/test_reference_cases.py"],
        resultados={"pytest": "5 passed"},
        evidencias={
            "token": segredo,
            "prompt": prompt,
            "diff_hash": "a" * TAMANHO_DIGEST,
        },
        limitacoes=["Nenhuma"],
    )
    assert segredo not in texto
    assert prompt not in texto
    assert "a" * TAMANHO_DIGEST in texto
