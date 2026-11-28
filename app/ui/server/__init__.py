"""API pública do servidor local da interface web."""

from app.ui.server.app import UiServer, create_server
from app.ui.server.auth import origem_valida, origin_local, pedido_autorizado
from app.ui.server.chat import ChatMessage, ChatService, ChatStore, serializar_mensagem
from app.ui.server.event_filters import (
    EventFilter,
    analisar_filtros,
    filtrar_evento,
    filtrar_eventos,
)
from app.ui.server.routes_approvals import (
    AGENTS_PATH,
    APPROVALS_PATH,
    emitir_aprovacao,
    listar_agentes,
)
from app.ui.server.routes_attachments import (
    ATTACHMENTS_PATH,
    RELEASE_PATH,
    caminhos_post,
    resposta_anexo,
)
from app.ui.server.routes_chat import CHAT_PATH, analisar_corpo, analisar_filtro_tarefa
from app.ui.server.routes_diff import (
    DIFF_PATH,
    analisar_consulta_diff,
    calcular_diff,
    calcular_diff_hash,
)
from app.ui.server.routes_events import EVENTS_PATH, gerar_eventos_sse
from app.ui.server.routes_llm_calls import (
    LLM_CALLS_PATH,
    analisar_filtro_correlacao,
    listar_chamadas,
)
from app.ui.server.routes_tasks import (
    TAREFAS_PATH,
    listar_tarefas,
    serializar_tarefa,
)
from app.ui.server.web_assets import WEB_FILES, ler_asset

__all__ = [
    "AGENTS_PATH",
    "APPROVALS_PATH",
    "ATTACHMENTS_PATH",
    "CHAT_PATH",
    "RELEASE_PATH",
    "DIFF_PATH",
    "EVENTS_PATH",
    "LLM_CALLS_PATH",
    "TAREFAS_PATH",
    "WEB_FILES",
    "ChatMessage",
    "ChatService",
    "ChatStore",
    "EventFilter",
    "UiServer",
    "analisar_consulta_diff",
    "analisar_corpo",
    "analisar_filtro_correlacao",
    "analisar_filtro_tarefa",
    "analisar_filtros",
    "calcular_diff",
    "calcular_diff_hash",
    "caminhos_post",
    "create_server",
    "emitir_aprovacao",
    "filtrar_evento",
    "filtrar_eventos",
    "gerar_eventos_sse",
    "listar_agentes",
    "listar_chamadas",
    "ler_asset",
    "listar_tarefas",
    "origin_local",
    "origem_valida",
    "pedido_autorizado",
    "resposta_anexo",
    "serializar_mensagem",
    "serializar_tarefa",
]
