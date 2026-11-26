"""Modelos imutáveis do executor simples com aprovação."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.core.results import ToolResult

if TYPE_CHECKING:
    from threading import Event

TIMEOUT_PADRAO_S = 30.0
TIMEOUT_MAXIMO_S = 300.0
HASH_SHA256_CHARS = 64
_HEXADECIMAL = frozenset("0123456789abcdef")


class ExecutionConfigError(ValueError):
    """Pedido de execução fora do contrato esperado."""


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Pedido de subprocesso ligado a uma aprovação verificável."""

    task_id: str
    correlation_id: str
    diff_hash: str
    approval_token: str = field(repr=False)
    command: tuple[str, ...]
    timeout_s: float = TIMEOUT_PADRAO_S
    cancel_event: Event | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Valida identificadores, comando e prazo antes de qualquer execução."""
        for nome in ("task_id", "correlation_id", "approval_token"):
            valor = getattr(self, nome)
            if not isinstance(valor, str) or not valor.strip():
                raise ExecutionConfigError(f"O campo {nome} é obrigatório.")
        if (
            len(self.diff_hash) != HASH_SHA256_CHARS
            or not set(self.diff_hash) <= _HEXADECIMAL
        ):
            raise ExecutionConfigError("diff_hash tem de ser SHA-256 hexadecimal.")
        comando = tuple(self.command)
        if not comando or any(not isinstance(arg, str) or not arg for arg in comando):
            raise ExecutionConfigError("command tem de conter argumentos não vazios.")
        object.__setattr__(self, "command", comando)
        if (
            isinstance(self.timeout_s, bool)
            or not isinstance(self.timeout_s, (int, float))
            or not 0 < self.timeout_s <= TIMEOUT_MAXIMO_S
        ):
            raise ExecutionConfigError("timeout_s tem de estar entre 0 e 300.")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Resultado verificável de uma tentativa de execução."""

    tool_result: ToolResult
    isolated: bool
    returncode: int | None = None
    workspace: str | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float | None = None

    def __post_init__(self) -> None:
        """Garante que o executor simples nunca se apresenta como isolado."""
        if self.isolated is not False:
            raise ExecutionConfigError("O executor simples não é isolado.")

    @property
    def error(self) -> str | None:
        """Devolve o erro do resultado da ferramenta."""
        return self.tool_result.error
