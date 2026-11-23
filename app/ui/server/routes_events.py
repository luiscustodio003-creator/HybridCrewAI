"""Stream Server-Sent Events lido do ficheiro JSONL de eventos."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

from app.core.events import Event
from app.ui.server.event_filters import EventFilter, filtrar_evento

EVENTS_PATH = "/api/events"
INTERVALO_SSE = 0.1
HEARTBEAT_SSE = 1.0


def _linhas(path: Path) -> list[str]:
    """Devolve as linhas actualmente persistidas no ficheiro."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as ficheiro:
        return ficheiro.read().splitlines()


def gerar_eventos_sse(
    path: Path,
    filtro: EventFilter,
    intervalo: float = INTERVALO_SSE,
    heartbeat: float = HEARTBEAT_SSE,
) -> Iterator[str]:
    """Produz quadros SSE para eventos novos que passam no filtro."""
    processadas = 0
    ultimo_sinal = time.monotonic()
    while True:
        linhas = _linhas(path)
        for linha in linhas[processadas:]:
            if not linha.strip():
                continue
            evento = Event.from_dict(json.loads(linha))
            if filtrar_evento(evento, filtro):
                corpo = json.dumps(evento.to_dict(), ensure_ascii=False)
                yield f"data: {corpo}\n\n"
        processadas = len(linhas)
        agora = time.monotonic()
        if agora - ultimo_sinal >= heartbeat:
            yield ": keepalive\n\n"
            ultimo_sinal = agora
        time.sleep(intervalo)
