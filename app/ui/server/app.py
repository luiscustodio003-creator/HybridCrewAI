"""Servidor HTTP local da interface web."""

from __future__ import annotations

import json
import select
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Final
from urllib.parse import urlsplit

from app.core.config import ConfigError, Settings
from app.core.tasks import SqliteTaskStore
from app.llm import configure_observability
from app.ui.server.auth import origem_valida, pedido_autorizado
from app.ui.server.event_filters import analisar_filtros
from app.ui.server.routes_events import EVENTS_PATH, gerar_eventos_sse
from app.ui.server.routes_llm_calls import (
    LLM_CALLS_PATH,
    analisar_filtro_correlacao,
    listar_chamadas,
)
from app.ui.server.routes_tasks import TAREFAS_PATH, listar_tarefas

LOCAL_HOST: Final = "127.0.0.1"
HEALTH_PATH: Final = "/health"
MAX_PORT: Final = 65535
PHASE: Final = 3


class UiServer(ThreadingHTTPServer):
    """Servidor threaded vinculado à configuração da interface."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        settings: Settings,
        store: SqliteTaskStore,
        event_path: Path,
    ) -> None:
        self.settings = settings
        self.store = store
        self.event_path = event_path
        self._stream_lock = Lock()
        self._streams = 0
        super().__init__(address, handler)

    @property
    def llm_calls_path(self) -> Path:
        """Caminho derivado do log de eventos para as chamadas LLM."""
        return self.event_path.parent / "llm_calls.jsonl"

    @property
    def streams(self) -> int:
        """Número de streams SSE actualmente abertos."""
        with self._stream_lock:
            return self._streams

    def iniciar_stream(self) -> None:
        """Regista um stream SSE activo."""
        with self._stream_lock:
            self._streams += 1

    def terminar_stream(self) -> None:
        """Remove um stream SSE terminado."""
        with self._stream_lock:
            self._streams -= 1


class _Handler(BaseHTTPRequestHandler):
    """Responde aos pedidos HTTP da verificação de saúde."""

    server: UiServer

    def do_GET(self) -> None:
        """Aplica as barreiras locais antes de servir a rota protegida."""
        caminho = urlsplit(self.path).path
        rotas = {HEALTH_PATH, TAREFAS_PATH, EVENTS_PATH, LLM_CALLS_PATH}
        if caminho not in rotas or not self.server.settings.ui_enabled:
            self.send_error(HTTPStatus.NOT_FOUND, "Recurso não encontrado")
            return
        if not origem_valida(self.headers.get("Origin"), self.server.server_port):
            self.send_error(HTTPStatus.FORBIDDEN, "Origem não autorizada")
            return
        if not pedido_autorizado(dict(self.headers.items()), self.server.settings):
            self.send_error(HTTPStatus.UNAUTHORIZED, "Não autorizado")
            return
        if caminho == HEALTH_PATH:
            self._health()
        elif caminho == TAREFAS_PATH:
            self._tasks()
        elif caminho == LLM_CALLS_PATH:
            self._llm_calls()
        else:
            self._events()

    def _health(self) -> None:
        """Devolve o estado mínimo do servidor sem dados sensíveis."""
        self._json(HTTPStatus.OK, {"status": "ok", "phase": PHASE})

    def _tasks(self) -> None:
        """Devolve o histórico persistido sem aceitar escrita por consulta."""
        self._json(HTTPStatus.OK, listar_tarefas(self.server.store))

    def _llm_calls(self) -> None:
        """Devolve chamadas LLM registadas, sem prompt completo nem segredos."""
        try:
            correlacao = analisar_filtro_correlacao(urlsplit(self.path).query)
            chamadas = listar_chamadas(self.server.llm_calls_path, correlacao)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._json(HTTPStatus.OK, chamadas)

    def _events(self) -> None:
        """Transmite eventos filtrados em formato Server-Sent Events."""
        try:
            filtro = analisar_filtros(urlsplit(self.path).query)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.server.iniciar_stream()
        try:
            for quadro in gerar_eventos_sse(self.server.event_path, filtro):
                if self._ligacao_fechada():
                    return
                self.wfile.write(quadro.encode("utf-8"))
                self.wfile.flush()
        except OSError:
            return
        finally:
            self.server.terminar_stream()

    def _ligacao_fechada(self) -> bool:
        """Detecta o fecho da ligação sem consumir dados do pedido."""
        try:
            prontos, _, _ = select.select([self.connection], [], [], 0)
            if not prontos:
                return False
            return self.connection.recv(1, socket.MSG_PEEK) == b""
        except OSError:
            return True

    def _json(
        self,
        status: HTTPStatus,
        payload: dict[str, object] | list[dict[str, object]],
    ) -> None:
        """Escreve uma resposta JSON curta e com tipo declarado."""
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, formato: str, *argumentos: object) -> None:
        """Evita escrever pedidos em logs com dados não controlados."""
        return


def create_server(
    settings: Settings,
    host: str = LOCAL_HOST,
    port: int = 0,
    store: SqliteTaskStore | None = None,
    event_path: Path | None = None,
) -> UiServer:
    """Cria um servidor local threaded, sem aceitar outros endereços."""
    if host != LOCAL_HOST:
        raise ConfigError(f"A interface web só pode vincular {LOCAL_HOST}; recebido {host!r}.")
    if not 0 <= port <= MAX_PORT:
        raise ConfigError(f"porta inválida {port!r}; use um valor entre 0 e {MAX_PORT}.")
    armazenamento = store or SqliteTaskStore(settings.sqlite_path)
    armazenamento.initialize()
    caminho_eventos = event_path or settings.event_log
    configure_observability(caminho_eventos.parent / "llm_calls.jsonl")
    return UiServer((host, port), _Handler, settings, armazenamento, caminho_eventos)
