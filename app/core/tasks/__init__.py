"""API pública do módulo de tarefas."""

from app.core.tasks.ids import generate_task_id
from app.core.tasks.model import Task, TaskSpec, new_task
from app.core.tasks.state_machine import (
    TaskStateError,
    TaskStatus,
    pode_transitar,
    transitar,
)
from app.core.tasks.store_sqlite import SqliteTaskStore
from app.core.tasks.time import utc_now

__all__ = [
    "Task",
    "TaskSpec",
    "TaskStateError",
    "TaskStatus",
    "SqliteTaskStore",
    "generate_task_id",
    "new_task",
    "pode_transitar",
    "transitar",
    "utc_now",
]
