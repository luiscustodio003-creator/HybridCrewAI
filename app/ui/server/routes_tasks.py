"""Leitura das tarefas persistidas pela interface web."""

from __future__ import annotations

from app.core.tasks import SqliteTaskStore, Task

TAREFAS_PATH = "/api/tasks"


def serializar_tarefa(tarefa: Task) -> dict[str, object]:
    """Converte uma tarefa num objeto JSON sem campos internos."""
    return {
        "task_id": tarefa.task_id,
        "correlation_id": tarefa.task_id,
        "title": tarefa.title,
        "description": tarefa.description,
        "agent": tarefa.agent,
        "phase": tarefa.phase,
        "status": tarefa.status.value,
        "created_at": tarefa.created_at.isoformat(),
        "updated_at": tarefa.updated_at.isoformat(),
        "attempts": tarefa.attempts,
    }


def listar_tarefas(store: SqliteTaskStore) -> list[dict[str, object]]:
    """Devolve o histórico persistido na ordem de criação."""
    return [serializar_tarefa(tarefa) for tarefa in store.list_tasks()]
