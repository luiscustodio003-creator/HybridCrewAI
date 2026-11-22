"""Logging estruturado com correlação, redacção e stack trace."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Mapping
from typing import TYPE_CHECKING, TextIO

from app.core.events import EventBus, EventLevel, new_event
from app.core.logging.correlation import bind_context, current_context, reset_context
from app.core.logging.redaction import SecretRegistry

if TYPE_CHECKING:
    from contextvars import Token

    from app.core.events import Event, EventContext

_NIVEIS = {
    EventLevel.DEBUG: 10,
    EventLevel.INFO: 20,
    EventLevel.WARNING: 30,
    EventLevel.ERROR: 40,
}


class LoggingError(RuntimeError):
    """Falha de configuração ou utilização do logging central."""


class LoggingContextError(LoggingError):
    """Não há contexto de correlação associado ao fluxo actual."""


class TextLogSink:
    """Destino legível por pessoas, sempre com redacção aplicada."""

    __slots__ = ("_registry", "_stream")

    def __init__(
        self, stream: TextIO | None = None, secrets: SecretRegistry | None = None
    ) -> None:
        self._stream = sys.stderr if stream is None else stream
        self._registry = secrets or SecretRegistry()

    def write(self, event: Event) -> None:
        """Escreve uma linha redigida com os campos de rastreabilidade."""
        partes = [
            f"[{event.occurred_at}] {event.level.name} {event.phase} "
            f"{event.correlation_id} {event.task_id} {event.agent} "
            f"{event.kind}: {event.message}"
        ]
        stack = event.data.get("stack_trace")
        if stack:
            partes.append(f"stack_trace: {stack}")
        self._stream.write(self._registry.redact("\n".join(partes)) + "\n")
        self._stream.flush()


class EventLogger:
    """Emite eventos de log para o barramento, com redacção obrigatória."""

    __slots__ = ("_bus", "_min_level", "_registry")

    def __init__(
        self,
        bus: EventBus,
        min_level: EventLevel = EventLevel.INFO,
        secrets: SecretRegistry | None = None,
    ) -> None:
        self._bus = bus
        self._min_level = min_level
        self._registry = secrets or SecretRegistry()

    def bind(self, context: EventContext) -> Token[EventContext | None]:
        """Associa um contexto ao fluxo actual."""
        return bind_context(context)

    def reset(self, token: Token[EventContext | None]) -> None:
        """Restaura o contexto anterior."""
        reset_context(token)

    def _emit(
        self,
        level: EventLevel,
        message: str,
        kind: str,
        data: Mapping[str, object] | None,
        exc_info: bool,
    ) -> Event | None:
        """Cria e publica um evento de log já redigido."""
        context = current_context()
        if context is None:
            raise LoggingContextError(
                "É necessário correlation_id: usar bind_context antes de registar logs."
            )
        if _NIVEIS[level] < _NIVEIS[self._min_level]:
            return None
        valores: dict[str, object] = {}
        for chave, valor in (data or {}).items():
            valores[chave] = self._registry.redact(valor) if isinstance(valor, str) else valor
        if exc_info:
            valores["stack_trace"] = self._registry.redact(traceback.format_exc())
        evento = new_event(
            context,
            kind=kind,
            message=self._registry.redact(message),
            level=level,
            data=valores,
        )
        self._bus.publish(evento)
        return evento

    def debug(
        self, message: str, *, kind: str = "log", data: Mapping[str, object] | None = None
    ) -> Event | None:
        """Regista um detalhe de depuração."""
        return self._emit(EventLevel.DEBUG, message, kind, data, False)

    def info(
        self, message: str, *, kind: str = "log", data: Mapping[str, object] | None = None
    ) -> Event | None:
        """Regista um facto normal."""
        return self._emit(EventLevel.INFO, message, kind, data, False)

    def warning(
        self, message: str, *, kind: str = "log", data: Mapping[str, object] | None = None
    ) -> Event | None:
        """Regista um aviso."""
        return self._emit(EventLevel.WARNING, message, kind, data, False)

    def error(
        self,
        message: str,
        *,
        kind: str = "log",
        data: Mapping[str, object] | None = None,
        exc_info: bool = False,
    ) -> Event | None:
        """Regista um erro, com stack trace quando pedido."""
        return self._emit(EventLevel.ERROR, message, kind, data, exc_info)


def configure_logging(
    bus: EventBus,
    stream: TextIO | None = None,
    secrets: SecretRegistry | None = None,
    min_level: EventLevel = EventLevel.INFO,
) -> EventLogger:
    """Liga um destino textual ao barramento e devolve o logger central."""
    registry = secrets or SecretRegistry()
    bus.subscribe(TextLogSink(stream, registry))
    return EventLogger(bus, min_level, registry)
