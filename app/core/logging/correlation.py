"""Contexto de correlação partilhado pelos registos de uma tarefa."""

from __future__ import annotations

from contextvars import ContextVar, Token

from app.core.events import EventContext

_CURRENT: ContextVar[EventContext | None] = ContextVar(
    "hcw_event_context", default=None
)


def bind_context(context: EventContext) -> Token[EventContext | None]:
    """Associa um contexto ao fluxo actual e devolve o token de reposição."""
    return _CURRENT.set(context)


def reset_context(token: Token[EventContext | None]) -> None:
    """Restaura o contexto anterior usando o token devolvido por bind_context."""
    _CURRENT.reset(token)


def current_context() -> EventContext | None:
    """Devolve o contexto activo, se houver."""
    return _CURRENT.get()
