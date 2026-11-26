"""Stream Server-Sent Events lido do ficheiro JSONL de eventos."""

from __future__ import annotations

import json
import select
import socket
import time
from collections.abc import Iterator
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Protocol, cast
from urllib.parse import urlsplit

from app.core.events import Event
from app.ui.server.event_filters import EventFilter, analisar_filtros, filtrar_evento

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


class _ServidorEventos(Protocol):
    """Servidor com contagem de streams usada pelo handler SSE."""

    event_path: Path

    def iniciar_stream(self) -> None: ...

    def terminar_stream(self) -> None: ...


def ligacao_fechada(handler: BaseHTTPRequestHandler) -> bool:
    """Detecta o fecho da ligação sem consumir dados do pedido."""
    try:
        prontos, _, _ = select.select([handler.connection], [], [], 0)
        if not prontos:
            return False
        return handler.connection.recv(1, socket.MSG_PEEK) == b""
    except OSError:
        return True


def transmitir_eventos(handler: BaseHTTPRequestHandler) -> None:
    """Transmite eventos filtrados em formato Server-Sent Events."""
    try:
        filtro = analisar_filtros(urlsplit(handler.path).query)
    except ValueError as exc:
        handler.send_error(HTTPStatus.BAD_REQUEST, str(exc))
        return
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "close")
    handler.end_headers()
    servidor = cast(_ServidorEventos, handler.server)
    servidor.iniciar_stream()
    try:
        for quadro in gerar_eventos_sse(servidor.event_path, filtro):
            if ligacao_fechada(handler):
                return
            handler.wfile.write(quadro.encode("utf-8"))
            handler.wfile.flush()
    except OSError:
        return
    finally:
        servidor.terminar_stream()
