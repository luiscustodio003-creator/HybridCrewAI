"""Testes do orçamento de tokens e de ferramentas."""

from __future__ import annotations

import pytest

from app.core.config.defaults import (
    DEFAULT_MAX_TOKENS_PER_TASK,
    DEFAULT_MAX_TOOLS_PER_REQUEST,
)
from app.core.events import Event, EventBus, EventContext
from app.llm.budget import (
    BudgetExceeded,
    BudgetLimits,
    TokenBudget,
    ToolSpec,
    estimate_tokens,
    select_tools,
)

MAX_DESC_TESTE = 40


class _Sink:
    def __init__(self) -> None:
        self.eventos: list[Event] = []

    def write(self, event: Event) -> None:
        self.eventos.append(event)


def test_estimativa_de_tokens_e_deterministica_e_sem_fornecedor() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0
    assert estimate_tokens("abc") == 1
    assert estimate_tokens("abc") == estimate_tokens("abc")
    assert estimate_tokens(" texto ") == estimate_tokens("texto")


def test_exceder_limite_gera_erro_tipado_e_evento_antes_da_chamada() -> None:
    sink = _Sink()
    contexto = EventContext(
        correlation_id="corr-007",
        task_id="HCW-02-007",
        agent="gateway",
        phase="2",
    )
    limites = BudgetLimits(
        max_tokens_per_request=2,
        max_tokens_per_task=DEFAULT_MAX_TOKENS_PER_TASK,
        max_tools=DEFAULT_MAX_TOOLS_PER_REQUEST,
    )
    orcamento = TokenBudget(limites, EventBus([sink]), contexto)

    with pytest.raises(BudgetExceeded, match="pedido"):
        orcamento.reserve("x" * 40)

    assert len(sink.eventos) == 1
    assert sink.eventos[0].kind == "budget.exceeded"
    estimativa = sink.eventos[0].data["estimated"]
    assert isinstance(estimativa, int)
    assert estimativa > limites.max_tokens_per_request


def test_ollama_recebe_lista_curta_com_descricoes_breves() -> None:
    ferramentas = [
        ToolSpec(name=f"ferramenta-{indice}", description="descrição longa " * 8)
        for indice in range(6)
    ]
    selecionadas = select_tools(
        ferramentas, max_tools=3, max_description_chars=MAX_DESC_TESTE
    )

    assert [item.name for item in selecionadas] == [
        "ferramenta-0",
        "ferramenta-1",
        "ferramenta-2",
    ]
    assert all(len(item.description) <= MAX_DESC_TESTE for item in selecionadas)
    assert select_tools(ferramentas, max_tools=0) == []
