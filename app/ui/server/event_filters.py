"""Filtros de correlation_id e nível para o stream de eventos."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from urllib.parse import parse_qs

from app.core.events import Event, EventLevel


@dataclass(frozen=True, slots=True)
class EventFilter:
    """Critérios opcionais de seleção de eventos."""

    correlation_id: str | None = None
    level: EventLevel | None = None


def _valor_unico(
    parametros: dict[str, list[str]],
    nome: str,
) -> str | None:
    """Lê um parâmetro de consulta sem aceitar repetição."""
    valores = parametros.get(nome)
    if not valores:
        return None
    if len(valores) != 1 or not valores[0].strip():
        raise ValueError(f"Parâmetro inválido: {nome}.")
    return valores[0]


def analisar_filtros(consulta: str) -> EventFilter:
    """Constrói um filtro a partir da query string correta."""
    parametros = parse_qs(consulta, keep_blank_values=True)
    correlation_id = _valor_unico(parametros, "correlation_id")
    nivel = _valor_unico(parametros, "level")
    if nivel is None:
        return EventFilter(correlation_id=correlation_id)
    try:
        return EventFilter(
            correlation_id=correlation_id,
            level=EventLevel(nivel),
        )
    except ValueError as exc:
        raise ValueError(f"Parâmetro inválido: level ({nivel!r}).") from exc


def filtrar_evento(evento: Event, filtro: EventFilter) -> bool:
    """Indica se o evento satisfaz todos os critérios."""
    if filtro.correlation_id is not None:
        if evento.correlation_id != filtro.correlation_id:
            return False
    if filtro.level is not None and evento.level != filtro.level:
        return False
    return True


def filtrar_eventos(eventos: Iterable[Event], filtro: EventFilter) -> Iterator[Event]:
    """Devolve apenas os eventos que satisfazem o filtro."""
    for evento in eventos:
        if filtrar_evento(evento, filtro):
            yield evento
