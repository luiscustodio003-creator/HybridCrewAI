"""Testes de classificação, retries e cooldown do roteador."""

from __future__ import annotations

from app.core.config.defaults import (
    DEFAULT_COOLDOWN_INVALID_RESPONSE_S,
    DEFAULT_COOLDOWN_RATE_LIMIT_S,
    DEFAULT_COOLDOWN_TIMEOUT_S,
)
from app.llm import ErrorKind, ProviderError, ProviderKind
from app.llm.router import (
    CooldownTracker,
    FakeClock,
    RetryDecision,
    RetryPolicy,
    classify_error,
)


class _HttpError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def _erro_provider() -> ProviderError:
    return ProviderError(
        provider=ProviderKind.OLLAMA,
        kind=ErrorKind.RATE_LIMIT,
        message="HTTP 429",
        task_id="HCW-02-008",
        correlation_id="corr-008",
        retryable=True,
    )


def test_timeout_http_429_e_resposta_invalida_sao_classificados_a_parte() -> None:
    assert classify_error(TimeoutError()) == ErrorKind.TIMEOUT
    assert classify_error(_HttpError(429)) == ErrorKind.RATE_LIMIT
    assert classify_error(ValueError("json invalido")) == ErrorKind.INVALID_RESPONSE
    assert classify_error(_erro_provider()) == ErrorKind.RATE_LIMIT


def test_retries_sao_limitados_e_jitter_pode_ser_desactivado() -> None:
    politica = RetryPolicy()

    assert politica.decide("timeout", 1, jitter=False) == RetryDecision(
        retry=True,
        attempt=1,
        delay_s=DEFAULT_COOLDOWN_TIMEOUT_S,
    )
    assert politica.decide("timeout", 2, jitter=False).retry is False
    assert politica.decide("rate_limit", 1, jitter=False).delay_s == (
        DEFAULT_COOLDOWN_RATE_LIMIT_S
    )
    assert politica.decide("invalid_response", 1, jitter=False).delay_s == (
        DEFAULT_COOLDOWN_INVALID_RESPONSE_S
    )
    assert politica.decide("auth", 1, jitter=False).retry is False


def test_cooldown_e_diferente_por_tipo_e_injetavel_por_relogio_falso() -> None:
    relogio = FakeClock(initial=100.0)
    cooldowns = CooldownTracker(relogio)

    cooldowns.activate("timeout")
    assert cooldowns.is_active("timeout")
    assert not cooldowns.is_active("rate_limit")
    assert cooldowns.remaining("timeout") == DEFAULT_COOLDOWN_TIMEOUT_S

    relogio.advance(DEFAULT_COOLDOWN_TIMEOUT_S)
    assert not cooldowns.is_active("timeout")

    cooldowns.activate("rate_limit")
    assert cooldowns.remaining("rate_limit") == DEFAULT_COOLDOWN_RATE_LIMIT_S
