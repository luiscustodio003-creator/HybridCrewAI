"""Classificação de falhas e política de retries do roteador."""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from app.core.config.defaults import (
    DEFAULT_COOLDOWN_INVALID_RESPONSE_S,
    DEFAULT_COOLDOWN_RATE_LIMIT_S,
    DEFAULT_COOLDOWN_TIMEOUT_S,
    DEFAULT_MAX_RETRY_ATTEMPTS,
    DEFAULT_RETRY_JITTER_FRACTION,
)
from app.llm import ErrorKind, ProviderError

TipoKind = ErrorKind | str

_COOLDOWN_PADRAO: dict[ErrorKind, float] = {
    ErrorKind.TIMEOUT: DEFAULT_COOLDOWN_TIMEOUT_S,
    ErrorKind.RATE_LIMIT: DEFAULT_COOLDOWN_RATE_LIMIT_S,
    ErrorKind.INVALID_RESPONSE: DEFAULT_COOLDOWN_INVALID_RESPONSE_S,
}
_RETRYAVEIS = frozenset(_COOLDOWN_PADRAO)
_HTTP_TOO_MANY_REQUESTS = 429


def normalize_error_kind(kind: TipoKind) -> ErrorKind:
    """Converte um identificador de erro para `ErrorKind`."""
    if isinstance(kind, ErrorKind):
        return kind
    if isinstance(kind, str):
        try:
            return ErrorKind(kind)
        except ValueError as exc:
            raise ValueError(f"kind de erro desconhecido: {kind!r}.") from exc
    raise TypeError("kind tem de ser ErrorKind ou string.")


def classify_error(erro: BaseException) -> ErrorKind:
    """Classifica uma falha numa categoria estável e independente de fornecedor."""
    if isinstance(erro, ProviderError):
        return erro.kind
    if isinstance(erro, TimeoutError):
        return ErrorKind.TIMEOUT
    for nome in ("status_code", "code"):
        if getattr(erro, nome, None) == _HTTP_TOO_MANY_REQUESTS:
            return ErrorKind.RATE_LIMIT
    if isinstance(erro, ValueError):
        return ErrorKind.INVALID_RESPONSE
    return ErrorKind.NETWORK


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Decisão de retry com atraso determinístico quando jitter está desligado."""

    retry: bool
    attempt: int
    delay_s: float


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Política curta de retries, sem sleep e com jitter opcional."""

    max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS
    jitter_fraction: float = DEFAULT_RETRY_JITTER_FRACTION
    delays: Mapping[ErrorKind, float] = field(
        default_factory=lambda: dict(_COOLDOWN_PADRAO)
    )

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_attempts, bool)
            or not isinstance(self.max_attempts, int)
            or self.max_attempts < 1
        ):
            raise ValueError("max_attempts tem de ser inteiro positivo.")
        if (
            isinstance(self.jitter_fraction, bool)
            or not isinstance(self.jitter_fraction, (int, float))
            or not math.isfinite(self.jitter_fraction)
            or not 0 <= self.jitter_fraction < 1
        ):
            raise ValueError("jitter_fraction tem de estar em [0, 1).")
        delay_normalizado = {
            normalize_error_kind(kind): float(valor)
            for kind, valor in self.delays.items()
        }
        if any(not math.isfinite(valor) or valor <= 0 for valor in delay_normalizado.values()):
            raise ValueError("delays tem de conter valores finitos positivos.")
        object.__setattr__(self, "delays", delay_normalizado)

    def is_retryable(self, kind: TipoKind) -> bool:
        """Indica se a categoria permite nova tentativa."""
        return normalize_error_kind(kind) in _RETRYAVEIS

    def delay_for(
        self,
        kind: TipoKind,
        attempt: int = 1,
        *,
        jitter: bool = False,
        rng: Callable[[], float] | None = None,
    ) -> float:
        """Devolve o atraso de retry; jitter desligado é determinístico."""
        tipo = normalize_error_kind(kind)
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise ValueError("attempt tem de ser inteiro positivo.")
        if not self.is_retryable(tipo):
            return 0.0
        base = self.delays[tipo] * (2 ** (attempt - 1))
        if not jitter:
            return base
        gerador = rng if rng is not None else random.random
        fator = gerador()
        if not math.isfinite(fator) or not 0 <= fator < 1:
            raise ValueError("rng tem de produzir valores em [0, 1).")
        return base * (1 + fator * self.jitter_fraction)

    def decide(
        self,
        kind: TipoKind,
        attempt: int,
        *,
        jitter: bool = False,
        rng: Callable[[], float] | None = None,
    ) -> RetryDecision:
        """Decide se há retry dentro do limite de tentativas por tipo."""
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise ValueError("attempt tem de ser inteiro positivo.")
        tipo = normalize_error_kind(kind)
        retry = self.is_retryable(tipo) and attempt < self.max_attempts
        atraso = self.delay_for(tipo, attempt, jitter=jitter, rng=rng) if retry else 0.0
        return RetryDecision(retry=retry, attempt=attempt, delay_s=atraso)
