"""Modelos imutáveis do fluxo CREATE e dos seus checkpoints."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from approvals.tokens import hash_diff_obrigatorio, texto_obrigatorio

from app.core.tasks import TaskStatus, utc_now

MAX_PEDIDO = 4000
MAX_CHAVE = 200
PADRAO_HASH = re.compile(r"[0-9a-f]{64}\Z")


class Step(StrEnum):
    """Passos verificáveis do fluxo CREATE."""

    PEDIDO = "pedido"
    REQUISITOS = "requisitos"
    PLANO = "plano"
    ARQUITECTURA = "arquitectura"
    APROVACAO = "aprovacao"
    EXECUCAO = "execucao"
    REVISAO = "revisao"
    RELATORIO = "relatorio"


PASSOS: tuple[Step, ...] = tuple(Step)


class WorkflowError(RuntimeError):
    """Falha verificável na execução do fluxo CREATE."""


class FluxoInativo(WorkflowError):
    """Configuração desactiva a criação guiada."""


class AprovacaoInvalida(WorkflowError):
    """Aprovação apresentada não corresponde ao fluxo."""


class EtapaFalhou(WorkflowError):
    """Uma etapa verificável não terminou com sucesso."""


def _texto(valor: str, campo: str, limite: int) -> str:
    if not isinstance(valor, str):
        raise ValueError(f"{campo} tem de ser texto.")
    resultado = valor.strip()
    if not resultado:
        raise ValueError(f"{campo} é obrigatório.")
    if len(resultado) > limite:
        raise ValueError(f"{campo} excede {limite} caracteres.")
    return resultado


def hash_token(valor: str) -> str:
    """Devolve o digest SHA-256 de um token sem o guardar em claro."""
    return hashlib.sha256(_texto(valor, "token", 512).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CreateRequest:
    """Pedido verificável para executar ou retomar um fluxo CREATE."""

    task_id: str
    correlation_id: str
    pedido: str
    diff_hash: str
    token_aprovacao: str | None = None
    chaves: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Valida identificadores, diff, token opcional e chaves por passo."""
        object.__setattr__(self, "task_id", texto_obrigatorio(self.task_id, "task_id"))
        object.__setattr__(
            self,
            "correlation_id",
            texto_obrigatorio(self.correlation_id, "correlation_id"),
        )
        object.__setattr__(self, "pedido", _texto(self.pedido, "pedido", MAX_PEDIDO))
        object.__setattr__(self, "diff_hash", hash_diff_obrigatorio(self.diff_hash))
        if self.token_aprovacao is not None:
            object.__setattr__(
                self, "token_aprovacao", _texto(self.token_aprovacao, "token", 512)
            )
        permitidas = {passo.value for passo in PASSOS}
        copia: dict[str, str] = {}
        for chave, valor in dict(self.chaves).items():
            if chave not in permitidas:
                raise ValueError(f"Chave de idempotência desconhecida: {chave}.")
            copia[chave] = _texto(valor, f"chave {chave}", MAX_CHAVE)
        object.__setattr__(self, "chaves", copia)

    def chave_para(self, passo: Step) -> str:
        """Devolve a chave de idempotência determinística de um passo."""
        return self.chaves.get(passo.value) or f"{self.task_id}:{passo.value}"


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """Estado persistido de um fluxo CREATE."""

    task_id: str
    correlation_id: str
    status: TaskStatus
    last_completed_step: Step | None
    pending_token_hash: str | None
    agent: str
    phase: str
    version: int = 1
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Valida identificadores, passo, hash pendente e metadados."""
        object.__setattr__(self, "task_id", texto_obrigatorio(self.task_id, "task_id"))
        object.__setattr__(
            self,
            "correlation_id",
            texto_obrigatorio(self.correlation_id, "correlation_id"),
        )
        if not isinstance(self.status, TaskStatus):
            raise ValueError("status tem de ser TaskStatus.")
        if self.last_completed_step is not None and not isinstance(
            self.last_completed_step, Step
        ):
            raise ValueError("last_completed_step tem de ser Step ou None.")
        if self.pending_token_hash is not None and not PADRAO_HASH.fullmatch(
            self.pending_token_hash
        ):
            raise ValueError("pending_token_hash tem de ser SHA-256 hexadecimal.")
        object.__setattr__(self, "agent", _texto(self.agent, "agent", 120))
        object.__setattr__(self, "phase", _texto(self.phase, "phase", 120))
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("version tem de ser inteiro positivo.")
        if not isinstance(self.updated_at, datetime) or self.updated_at.tzinfo is None:
            raise ValueError("updated_at tem de ser UTC.")

    def to_dict(self) -> dict[str, object]:
        """Projecta o checkpoint sem expor o valor do token."""
        return {
            "task_id": self.task_id,
            "correlation_id": self.correlation_id,
            "status": self.status.value,
            "last_completed_step": (
                self.last_completed_step.value if self.last_completed_step else None
            ),
            "pending_token_hash": self.pending_token_hash,
            "agent": self.agent,
            "phase": self.phase,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Resultado verificável de uma execução ou retomada."""

    task_id: str
    correlation_id: str
    checkpoint: Checkpoint
    aguardando_aprovacao: bool
    evidencias: tuple[str, ...] = ()

    @property
    def status(self) -> TaskStatus:
        """Devolve o estado actual da tarefa."""
        return self.checkpoint.status

    @property
    def last_completed_step(self) -> Step | None:
        """Devolve o último passo confirmado."""
        return self.checkpoint.last_completed_step
