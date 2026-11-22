"""Controlo determinístico de tokens por pedido e por tarefa."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.core.config.defaults import (
    DEFAULT_MAX_TOKENS_PER_REQUEST,
    DEFAULT_MAX_TOKENS_PER_TASK,
    DEFAULT_MAX_TOOL_DESCRIPTION_CHARS,
    DEFAULT_MAX_TOOLS_PER_REQUEST,
)
from app.core.events import EventBus, EventContext, EventLevel, new_event


class BudgetExceeded(RuntimeError):
    """Limite de orçamento atingido antes da chamada ao modelo."""


@dataclass(frozen=True, slots=True)
class BudgetLimits:
    """Limites lidos da configuração central."""

    max_tokens_per_request: int = DEFAULT_MAX_TOKENS_PER_REQUEST
    max_tokens_per_task: int = DEFAULT_MAX_TOKENS_PER_TASK
    max_tools: int = DEFAULT_MAX_TOOLS_PER_REQUEST
    max_tool_description_chars: int = DEFAULT_MAX_TOOL_DESCRIPTION_CHARS

    def __post_init__(self) -> None:
        for nome in (
            "max_tokens_per_request",
            "max_tokens_per_task",
            "max_tools",
            "max_tool_description_chars",
        ):
            valor = getattr(self, nome)
            if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
                raise ValueError(f"{nome} tem de ser inteiro positivo.")


def estimate_tokens(texto: str) -> int:
    """Estima tokens sem depender de fornecedor nem de biblioteca externa."""
    if not isinstance(texto, str):
        raise TypeError("texto tem de ser string.")
    return math.ceil(len(texto.strip()) / 4)


@dataclass(slots=True)
class TokenBudget:
    """Reserva tokens e publica eventos quando um limite é excedido."""

    limits: BudgetLimits
    bus: EventBus | None = None
    context: EventContext | None = None
    _consumido: dict[str, int] = field(default_factory=dict)

    def _publicar_excesso(self, escopo: str, estimativa: int, limite: int) -> None:
        if self.bus is None or self.context is None:
            return
        self.bus.publish(
            new_event(
                self.context,
                kind="budget.exceeded",
                message=f"Orçamento de tokens excedido no {escopo}.",
                level=EventLevel.WARNING,
                data={
                    "escopo": escopo,
                    "estimated": estimativa,
                    "limit": limite,
                },
            )
        )

    def reserve(self, texto: str) -> int:
        """Valida e regista o custo estimado antes de qualquer chamada."""
        estimativa = estimate_tokens(texto)
        if estimativa > self.limits.max_tokens_per_request:
            self._publicar_excesso(
                "pedido", estimativa, self.limits.max_tokens_per_request
            )
            raise BudgetExceeded(
                f"Orçamento excedido no pedido: {estimativa} > "
                f"{self.limits.max_tokens_per_request} tokens."
            )
        chave = self.context.task_id if self.context is not None else "sem-contexto"
        total = self._consumido.get(chave, 0) + estimativa
        if total > self.limits.max_tokens_per_task:
            self._publicar_excesso("tarefa", total, self.limits.max_tokens_per_task)
            raise BudgetExceeded(
                f"Orçamento excedido na tarefa: {total} > "
                f"{self.limits.max_tokens_per_task} tokens."
            )
        self._consumido[chave] = total
        return estimativa
