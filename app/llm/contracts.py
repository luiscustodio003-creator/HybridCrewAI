"""Contratos imutáveis do gateway de modelos, sem tipos de SDK externo."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum, StrEnum

from app.core.logging import SecretRegistry

_REDACTED = "***REDACTED***"
_PADRAO_AWS = re.compile(r"AKIA[0-9A-Z]{16}")
_PADRAO_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_PADRAO_ATRIBUICAO = re.compile(
    r"(?i)\b([A-Z_][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)\s*[:=]\s*)([^\s,;]+)"
)


class ProviderKind(StrEnum):
    """Fornecedores permitidos, sem fuga de tipos de SDK; EXTERNAL é só política."""

    GEMINI_TEXT = "gemini-text"
    GEMINI_LIVE = "gemini-live"
    OLLAMA = "ollama"
    FAKE = "fake"
    EXTERNAL = "external"


class ErrorKind(StrEnum):
    """Categorias de falha independentes de fornecedor."""

    AUTH = "auth"
    BUDGET = "budget"
    CONSENT = "consent"
    INVALID_RESPONSE = "invalid_response"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"


def _redigir(texto: str) -> str:
    """Remove segredos antes de qualquer representação textual."""
    resultado = SecretRegistry().redact(texto)
    resultado = _PADRAO_ATRIBUICAO.sub(rf"\1{_REDACTED}", resultado)
    resultado = _PADRAO_AWS.sub(_REDACTED, resultado)
    return _PADRAO_BEARER.sub(f"Bearer {_REDACTED}", resultado)


def _validar_texto(valor: object, nome: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nome} tem de ser texto não vazio.")
    return valor


def _validar_inteiro(valor: object, nome: str, minimo: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < minimo:
        raise ValueError(f"{nome} tem de ser inteiro >= {minimo}.")
    return valor


def _validar_numero(valor: object, nome: str, *, positivo: bool) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nome} tem de ser número.")
    numero = float(valor)
    if not math.isfinite(numero) or (numero <= 0 if positivo else numero < 0):
        limite = "> 0" if positivo else ">= 0"
        raise ValueError(f"{nome} tem de ser finito e {limite}.")
    return numero


def _validar_enum(valor: object, tipo: type[Enum], nome: str) -> Enum:
    if not isinstance(valor, tipo):
        raise TypeError(f"{nome} tem de ser {tipo.__name__}.")
    return valor


@dataclass(frozen=True, repr=False)
class ModelRequest:
    """Pedido de modelo com timeout obrigatório e fornecedor explícito."""

    provider: ProviderKind
    model: str
    prompt: str
    timeout_s: float
    task_id: str
    correlation_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider", _validar_enum(self.provider, ProviderKind, "provider")
        )
        object.__setattr__(self, "model", _validar_texto(self.model, "model"))
        object.__setattr__(self, "prompt", _validar_texto(self.prompt, "prompt"))
        object.__setattr__(
            self, "timeout_s", _validar_numero(self.timeout_s, "timeout_s", positivo=True)
        )
        object.__setattr__(self, "task_id", _validar_texto(self.task_id, "task_id"))
        object.__setattr__(
            self, "correlation_id", _validar_texto(self.correlation_id, "correlation_id")
        )

    def __repr__(self) -> str:
        return (
            f"ModelRequest(provider={self.provider.value!r}, model={_redigir(self.model)!r}, "
            f"prompt={_redigir(self.prompt)!r}, timeout_s={self.timeout_s!r}, "
            f"task_id={self.task_id!r}, correlation_id={self.correlation_id!r})"
        )


@dataclass(frozen=True, repr=False)
class ModelResponse:
    """Resposta normalizada de qualquer fornecedor."""

    provider: ProviderKind
    model: str
    text: str
    task_id: str
    correlation_id: str
    latency_ms: float
    tokens_used: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider", _validar_enum(self.provider, ProviderKind, "provider")
        )
        object.__setattr__(self, "model", _validar_texto(self.model, "model"))
        object.__setattr__(self, "text", _validar_texto(self.text, "text"))
        object.__setattr__(self, "task_id", _validar_texto(self.task_id, "task_id"))
        object.__setattr__(
            self, "correlation_id", _validar_texto(self.correlation_id, "correlation_id")
        )
        object.__setattr__(
            self,
            "latency_ms",
            _validar_numero(self.latency_ms, "latency_ms", positivo=False),
        )
        if self.tokens_used is not None:
            object.__setattr__(
                self,
                "tokens_used",
                _validar_inteiro(self.tokens_used, "tokens_used", 0),
            )

    def __repr__(self) -> str:
        return (
            f"ModelResponse(provider={self.provider.value!r}, model={_redigir(self.model)!r}, "
            f"text={_redigir(self.text)!r}, task_id={self.task_id!r}, "
            f"correlation_id={self.correlation_id!r}, latency_ms={self.latency_ms!r}, "
            f"tokens_used={self.tokens_used!r})"
        )


@dataclass(frozen=True, repr=False)
class ProviderError(Exception):
    """Falha de fornecedor com categoria estável e mensagem redigida."""

    provider: ProviderKind
    kind: ErrorKind
    message: str
    task_id: str
    correlation_id: str
    retryable: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider", _validar_enum(self.provider, ProviderKind, "provider")
        )
        object.__setattr__(self, "kind", _validar_enum(self.kind, ErrorKind, "kind"))
        object.__setattr__(self, "message", _validar_texto(self.message, "message"))
        object.__setattr__(self, "task_id", _validar_texto(self.task_id, "task_id"))
        object.__setattr__(
            self, "correlation_id", _validar_texto(self.correlation_id, "correlation_id")
        )
        if not isinstance(self.retryable, bool):
            raise ValueError("retryable tem de ser booleano.")
        object.__setattr__(self, "args", (self.__str__(),))

    def __repr__(self) -> str:
        return (
            f"ProviderError(provider={self.provider.value!r}, kind={self.kind.value!r}, "
            f"message={self.__str__()!r}, task_id={self.task_id!r}, "
            f"correlation_id={self.correlation_id!r}, retryable={self.retryable!r})"
        )

    def __str__(self) -> str:
        return _redigir(self.message)
