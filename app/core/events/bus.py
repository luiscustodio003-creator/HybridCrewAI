"""Barramento de eventos em memória."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from app.core.events.models import Event


class EventSink(Protocol):
    """Destino que recebe eventos já validados."""

    def write(self, event: Event) -> None:
        """Processa um evento."""
        ...


class EventBusError(RuntimeError):
    """Pelo menos um destino falhou ao processar o evento."""


class EventBus:
    """Entrega eventos a todos os destinos registados."""

    __slots__ = ("_sinks",)

    def __init__(self, sinks: Iterable[EventSink] = ()) -> None:
        self._sinks = list(sinks)

    def subscribe(self, sink: EventSink) -> None:
        """Regista um destino adicional."""
        self._sinks.append(sink)

    def publish(self, event: Event) -> None:
        """Entrega o evento a todos os destinos, mesmo que um falhe."""
        falhas: list[Exception] = []
        for sink in self._sinks:
            try:
                sink.write(event)
            except Exception as exc:  # noqa: BLE001
                falhas.append(exc)
        if falhas:
            raise EventBusError(
                f"{len(falhas)} destino(s) falharam ao processar {event.kind}."
            ) from falhas[0]
