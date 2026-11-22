"""Modelo imutável de uma tarefa do agente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.tasks.ids import generate_task_id
from app.core.tasks.state_machine import TaskStatus
from app.core.tasks.time import utc_now


def _texto_obrigatorio(valor: str, campo: str) -> str:
    """Valida e normaliza um campo textual obrigatório."""
    texto = valor.strip()
    if not texto:
        raise ValueError(f"O campo {campo} é obrigatório.")
    return texto


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Dados de entrada para criar uma tarefa."""

    title: str
    description: str
    agent: str
    phase: str
    chave: str
    status: TaskStatus = TaskStatus.CREATED


@dataclass(frozen=True, slots=True)
class Task:
    """Tarefa imutável com rastreabilidade temporal."""

    task_id: str
    title: str
    description: str
    agent: str
    phase: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    attempts: int

    def __post_init__(self) -> None:
        """Valida os campos e normaliza texto."""
        object.__setattr__(self, "title", _texto_obrigatorio(self.title, "title"))
        object.__setattr__(
            self, "description", _texto_obrigatorio(self.description, "description")
        )
        object.__setattr__(self, "agent", _texto_obrigatorio(self.agent, "agent"))
        object.__setattr__(self, "phase", _texto_obrigatorio(self.phase, "phase"))
        if not self.task_id:
            raise ValueError("O campo task_id é obrigatório.")
        if self.attempts < 0:
            raise ValueError("O campo attempts não pode ser negativo.")


def new_task(spec: TaskSpec) -> Task:
    """Cria uma tarefa com identificador estável e horas UTC."""
    agora = utc_now()
    return Task(
        task_id=generate_task_id(spec.chave),
        title=spec.title,
        description=spec.description,
        agent=spec.agent,
        phase=spec.phase,
        status=spec.status,
        created_at=agora,
        updated_at=agora,
        attempts=0,
    )
