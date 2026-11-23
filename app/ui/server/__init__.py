"""API pública do servidor local da interface web."""

from app.ui.server.app import create_server
from app.ui.server.auth import origem_valida, origin_local, pedido_autorizado
from app.ui.server.event_filters import (
    EventFilter,
    analisar_filtros,
    filtrar_evento,
    filtrar_eventos,
)
from app.ui.server.routes_events import EVENTS_PATH, gerar_eventos_sse
from app.ui.server.routes_tasks import (
    TAREFAS_PATH,
    listar_tarefas,
    serializar_tarefa,
)

__all__ = [
    "EVENTS_PATH",
    "TAREFAS_PATH",
    "EventFilter",
    "analisar_filtros",
    "create_server",
    "filtrar_evento",
    "filtrar_eventos",
    "gerar_eventos_sse",
    "listar_tarefas",
    "origin_local",
    "origem_valida",
    "pedido_autorizado",
    "serializar_tarefa",
]
