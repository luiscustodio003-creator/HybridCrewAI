"""Transições válidas do ciclo de vida de uma tarefa."""

from __future__ import annotations

from dataclasses import replace
from enum import StrEnum
from typing import TYPE_CHECKING

from app.core.tasks.time import utc_now

if TYPE_CHECKING:
    from app.core.tasks.model import Task


class TaskStatus(StrEnum):
    """Estados possíveis de uma tarefa."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStateError(ValueError):
    """Transição de estado não permitida."""


_TRANSICOES: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.QUEUED, TaskStatus.CANCELLED}),
    TaskStatus.QUEUED: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.INTERRUPTED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.INTERRUPTED: frozenset(
        {TaskStatus.QUEUED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


def pode_transitar(origem: TaskStatus, destino: TaskStatus) -> bool:
    """Indica se a transição entre estados é permitida."""
    return destino in _TRANSICOES.get(origem, frozenset())


def transitar(tarefa: Task, destino: TaskStatus) -> Task:
    """Aplica uma transição válida e devolve uma nova tarefa."""
    if not pode_transitar(tarefa.status, destino):
        raise TaskStateError(
            f"Transição inválida: {tarefa.status.name} para {destino.name}."
        )
    tentativas = tarefa.attempts + 1 if destino is TaskStatus.RUNNING else tarefa.attempts
    return replace(
        tarefa, status=destino, updated_at=utc_now(), attempts=tentativas
    )
