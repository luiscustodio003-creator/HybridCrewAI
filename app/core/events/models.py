"""Modelo imutável de eventos do sistema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

_CAMPOS_OBRIGATORIOS = (
    "correlation_id",
    "task_id",
    "agent",
    "phase",
    "kind",
    "message",
)


class EventLevel(StrEnum):
    """Níveis de severidade de um evento."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EventError(ValueError):
    """Base para erros de eventos."""


class EventValidationError(EventError):
    """Evento com campos ausentes, vazios ou com tipo inválido."""


def _texto_obrigatorio(nome: str, valor: object) -> str:
    """Valida um campo de texto obrigatório."""
    if not isinstance(valor, str) or not valor.strip():
        raise EventValidationError(f"Campo obrigatório inválido: {nome}.")
    return valor


@dataclass(frozen=True, slots=True)
class EventContext:
    """Contexto obrigatório partilhado por todos os eventos de uma tarefa."""

    correlation_id: str
    task_id: str
    agent: str
    phase: str

    def __post_init__(self) -> None:
        """Valida os quatro campos de rastreabilidade."""
        _texto_obrigatorio("correlation_id", self.correlation_id)
        _texto_obrigatorio("task_id", self.task_id)
        _texto_obrigatorio("agent", self.agent)
        _texto_obrigatorio("phase", self.phase)


@dataclass(frozen=True, slots=True)
class Event:
    """Um facto observado, independente e serializável."""

    event_id: str
    occurred_at: str
    correlation_id: str
    task_id: str
    agent: str
    phase: str
    level: EventLevel
    kind: str
    message: str
    data: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Valida os campos obrigatórios de identificação."""
        _texto_obrigatorio("event_id", self.event_id)
        _texto_obrigatorio("occurred_at", self.occurred_at)
        for nome in _CAMPOS_OBRIGATORIOS:
            _texto_obrigatorio(nome, getattr(self, nome))
        if not isinstance(self.level, EventLevel):
            raise EventValidationError("Campo obrigatório inválido: level.")
        if not isinstance(self.data, dict):
            raise EventValidationError("Campo obrigatório inválido: data.")

    def to_dict(self) -> dict[str, object]:
        """Devolve uma representação plana, pronta para JSON."""
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "task_id": self.task_id,
            "agent": self.agent,
            "phase": self.phase,
            "level": self.level.value,
            "kind": self.kind,
            "message": self.message,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> Event:
        """Reconstrói um evento a partir de um objecto JSON."""
        try:
            level = EventLevel(str(payload["level"]))
        except (KeyError, ValueError) as exc:
            raise EventValidationError("Campo obrigatório inválido: level.") from exc
        data = payload.get("data", {})
        if not isinstance(data, dict):
            raise EventValidationError("Campo obrigatório inválido: data.")
        return cls(
            event_id=_texto_obrigatorio("event_id", payload.get("event_id")),
            occurred_at=_texto_obrigatorio("occurred_at", payload.get("occurred_at")),
            correlation_id=_texto_obrigatorio(
                "correlation_id", payload.get("correlation_id")
            ),
            task_id=_texto_obrigatorio("task_id", payload.get("task_id")),
            agent=_texto_obrigatorio("agent", payload.get("agent")),
            phase=_texto_obrigatorio("phase", payload.get("phase")),
            level=level,
            kind=_texto_obrigatorio("kind", payload.get("kind")),
            message=_texto_obrigatorio("message", payload.get("message")),
            data=dict(data),
        )


def new_event(
    context: EventContext,
    /,
    kind: str,
    message: str,
    level: EventLevel = EventLevel.INFO,
    data: Mapping[str, object] | None = None,
) -> Event:
    """Cria um evento com identificador e hora UTC gerados."""
    return Event(
        event_id=str(uuid4()),
        occurred_at=datetime.now(UTC).isoformat(),
        correlation_id=context.correlation_id,
        task_id=context.task_id,
        agent=context.agent,
        phase=context.phase,
        level=level,
        kind=kind,
        message=message,
        data={} if data is None else dict(data),
    )
