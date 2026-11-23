"""Filtros aplicados ao stream de eventos da interface web."""

from __future__ import annotations

import pytest

from app.core.events import Event, EventContext, EventLevel, new_event
from app.ui.server.event_filters import (
    EventFilter,
    analisar_filtros,
    filtrar_eventos,
)

TOTAL_EVENTOS = 3
CONTEXTO = EventContext(
    correlation_id="corr-1",
    task_id="task-1",
    agent="open-code",
    phase="3",
)


def _eventos() -> list[Event]:
    """Cria eventos com duas correlações e dois níveis."""
    return [
        new_event(CONTEXTO, kind="start", message="iniciar", level=EventLevel.INFO),
        new_event(CONTEXTO, kind="warn", message="avisar", level=EventLevel.WARNING),
        new_event(
            EventContext(
                correlation_id="corr-2",
                task_id="task-2",
                agent="open-code",
                phase="3",
            ),
            kind="warn",
            message="outro aviso",
            level=EventLevel.WARNING,
        ),
    ]


def test_analisar_filtros_com_correlacao_e_nivel() -> None:
    filtro = analisar_filtros("correlation_id=corr-1&level=warning")

    assert filtro == EventFilter(correlation_id="corr-1", level=EventLevel.WARNING)


def test_analisar_filtros_rejeita_nivel_desconhecido() -> None:
    with pytest.raises(ValueError, match="level"):
        analisar_filtros("level=critico")


def test_filtrar_eventos_pelos_dois_criterios() -> None:
    filtro = EventFilter(correlation_id="corr-1", level=EventLevel.WARNING)

    selecionados = list(filtrar_eventos(_eventos(), filtro))

    assert [evento.message for evento in selecionados] == ["avisar"]


def test_filtro_sem_criterios_devolve_todos() -> None:
    selecionados = list(filtrar_eventos(_eventos(), EventFilter()))

    assert len(selecionados) == TOTAL_EVENTOS
