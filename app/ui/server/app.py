"""Servidor HTTP local da interface web."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Final
from urllib.parse import urlsplit

from approvals.tokens import TokenStore

from app.core.config import ConfigError, Settings
from app.core.tasks import SqliteTaskStore
from app.llm import ProviderError, configure_observability
from app.ui.server.auth import origem_valida, pedido_autorizado
from app.ui.server.chat import ChatService, ChatStore, serializar_mensagem
from app.ui.server.http_responses import enviar_asset, enviar_json
from app.ui.server.routes_approvals import (
    AGENTS_PATH,
    APPROVALS_PATH,
    resposta_agentes,
    resposta_aprovacao,
)
from app.ui.server.routes_attachments import caminhos_post, resposta_anexo
from app.ui.server.routes_chat import (
    CHAT_PATH,
    MAX_CORPO_BYTES,
    analisar_corpo,
    analisar_filtro_tarefa,
)
from app.ui.server.routes_diff import DIFF_PATH, processar_diff
from app.ui.server.routes_events import EVENTS_PATH, transmitir_eventos
from app.ui.server.routes_llm_calls import (
    LLM_CALLS_PATH,
    analisar_filtro_correlacao,
    listar_chamadas,
)
from app.ui.server.routes_tasks import TAREFAS_PATH, listar_tarefas
from app.ui.server.web_assets import ler_asset

LOCAL_HOST: Final = "127.0.0.1"
HEALTH_PATH: Final = "/health"
MAX_PORT: Final = 65535
PHASE: Final = 3
GET_ROTAS: Final = frozenset(
    {HEALTH_PATH, TAREFAS_PATH, EVENTS_PATH, LLM_CALLS_PATH, CHAT_PATH, AGENTS_PATH, DIFF_PATH}
)


class UiServer(ThreadingHTTPServer):
    """Servidor threaded vinculado à configuração da interface."""

    allow_reuse_address = True
    daemon_threads = True
    chat_service: ChatService
    tokens: TokenStore

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
        """Serve recursos locais ou aplica barreiras às rotas protegidas."""
        caminho = urlsplit(self.path).path
        if not self.server.settings.ui_enabled:
            self.send_error(HTTPStatus.NOT_FOUND, "Recurso não encontrado")
            return
        recurso = ler_asset(caminho)
        if recurso is not None:
            enviar_asset(self, *recurso)
            return
        if caminho not in GET_ROTAS:
            self.send_error(HTTPStatus.NOT_FOUND, "Recurso não encontrado")
            return
        origem = self.headers.get("Origin")
        sec_fetch_site = self.headers.get("Sec-Fetch-Site")
        if not origem_valida(origem, self.server.server_port, sec_fetch_site):
            self.send_error(HTTPStatus.FORBIDDEN, "Origem não autorizada")
            return
        if not pedido_autorizado(dict(self.headers.items()), self.server.settings):
            self.send_error(HTTPStatus.UNAUTHORIZED, "Não autorizado")
            return
        if caminho == HEALTH_PATH:
            self._health()
        elif caminho == TAREFAS_PATH:
            self._tasks()
        elif caminho == AGENTS_PATH:
            self._agents()
        elif caminho == DIFF_PATH:
            self._diff()
        elif caminho == LLM_CALLS_PATH:
            self._llm_calls()
        elif caminho == CHAT_PATH:
            self._chat_historico()
        else:
            self._events()

    def _recusar_post(self, status: HTTPStatus, mensagem: str) -> None:
        """Drena o corpo antes de recusar para não abortar a ligação do cliente."""
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tamanho = 0
        if tamanho > 0:
            self.rfile.read(min(tamanho, MAX_CORPO_BYTES))
        self.send_error(status, mensagem)

    def do_POST(self) -> None:
        """Recebe mensagens, aprovações e anexos após as barreiras locais."""
        caminho = urlsplit(self.path).path
        rotas = {CHAT_PATH, APPROVALS_PATH} | caminhos_post(self.server.settings)
        if caminho not in rotas or not self.server.settings.ui_enabled:
            self._recusar_post(HTTPStatus.NOT_FOUND, "Recurso não encontrado")
            return
        origem = self.headers.get("Origin")
        sec_fetch_site = self.headers.get("Sec-Fetch-Site")
        if not origem_valida(origem, self.server.server_port, sec_fetch_site):
            self._recusar_post(HTTPStatus.FORBIDDEN, "Origem não autorizada")
            return
        if not pedido_autorizado(dict(self.headers.items()), self.server.settings):
            self._recusar_post(HTTPStatus.UNAUTHORIZED, "Não autorizado")
            return
        if caminho == CHAT_PATH:
            self._chat_post()
        elif caminho == APPROVALS_PATH:
            self._approvals_post()
        else:
            self._anexos_post(caminho)

    def _health(self) -> None:
        enviar_json(self, HTTPStatus.OK, {"status": "ok", "phase": PHASE})

    def _tasks(self) -> None:
        enviar_json(self, HTTPStatus.OK, listar_tarefas(self.server.store))

    def _agents(self) -> None:
        enviar_json(self, *resposta_agentes())

    def _diff(self) -> None:
        """Devolve o hash verificado entre o snapshot e o estado actual."""
        estado, resposta = processar_diff(
            self.server.settings, urlsplit(self.path).query
        )
        enviar_json(self, estado, resposta)

    def _approvals_post(self) -> None:
        """Emite um token de aprovação para um diff e uma tarefa válidos."""
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= MAX_CORPO_BYTES:
                raise ValueError("O corpo do pedido é obrigatório e está limitado.")
            corpo = self.rfile.read(tamanho)
        except ValueError as exc:
            enviar_json(self, HTTPStatus.BAD_REQUEST, {"error": {"message": str(exc)}})
            return
        resposta = resposta_aprovacao(
            self.server.tokens,
            self.server.server_port,
            dict(self.headers.items()),
            corpo,
            MAX_CORPO_BYTES,
        )
        enviar_json(self, *resposta)

    def _anexos_post(self, caminho: str) -> None:
        """Processa uploads e libertações com limites próprios."""
        estado, resposta = resposta_anexo(
            self, self.server.settings, self.server.tokens,
            self.server.chat_service, caminho,
        )
        enviar_json(self, estado, resposta)

    def _llm_calls(self) -> None:
        """Devolve chamadas LLM registadas, sem prompt completo nem segredos."""
        try:
            correlacao = analisar_filtro_correlacao(urlsplit(self.path).query)
            chamadas = listar_chamadas(self.server.llm_calls_path, correlacao)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        enviar_json(self, HTTPStatus.OK, chamadas)

    def _chat_historico(self) -> None:
        """Devolve o histórico persistido, opcionalmente filtrado por tarefa."""
        try:
            tarefa = analisar_filtro_tarefa(urlsplit(self.path).query)
        except ValueError as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        mensagens = self.server.chat_service.store.list_messages(tarefa)
        enviar_json(
            self, HTTPStatus.OK, [serializar_mensagem(item) for item in mensagens]
        )

    def _chat_post(self) -> None:
        """Envia a mensagem ao gateway e devolve a resposta persistida."""
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= MAX_CORPO_BYTES:
                raise ValueError("O corpo do pedido é obrigatório e está limitado.")
            mensagem, tarefa, correlacao = analisar_corpo(self.rfile.read(tamanho))
            resposta = self.server.chat_service.enviar(
                mensagem, task_id=tarefa, correlation_id=correlacao
            )
        except ValueError as exc:
            enviar_json(self, HTTPStatus.BAD_REQUEST, {"error": {"message": str(exc)}})
            return
        except ProviderError as exc:
            enviar_json(
                self,
                HTTPStatus.BAD_GATEWAY,
                {
                    "error": {
                        "kind": exc.kind.value,
                        "message": str(exc),
                        "task_id": exc.task_id,
                        "correlation_id": exc.correlation_id,
                    }
                },
            )
            return
        enviar_json(self, HTTPStatus.OK, serializar_mensagem(resposta))

    def _events(self) -> None:
        transmitir_eventos(self)

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
        raise ConfigError(
            f"A interface web só pode vincular {LOCAL_HOST}; recebido {host!r}."
        )
    if not 0 <= port <= MAX_PORT:
        raise ConfigError(
            f"porta inválida {port!r}; use um valor entre 0 e {MAX_PORT}."
        )
    armazenamento = store or SqliteTaskStore(settings.sqlite_path)
    armazenamento.initialize()
    chat_store = ChatStore(armazenamento.path)
    chat_store.initialize()
    caminho_eventos = event_path or settings.event_log
    configure_observability(caminho_eventos.parent / "llm_calls.jsonl")
    servidor = UiServer(
        (host, port), _Handler, settings, armazenamento, caminho_eventos
    )
    servidor.chat_service = ChatService(chat_store)
    servidor.tokens = TokenStore(settings)
    return servidor
