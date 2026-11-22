"""Cooldowns por tipo de erro com relógio injetável."""

from __future__ import annotations

import math
from collections.abc import Mapping
from time import monotonic
from typing import Protocol

from app.core.config.defaults import (
    DEFAULT_COOLDOWN_INVALID_RESPONSE_S,
    DEFAULT_COOLDOWN_RATE_LIMIT_S,
    DEFAULT_COOLDOWN_TIMEOUT_S,
)
from app.llm import ErrorKind
from app.llm.router.errors import TipoKind, normalize_error_kind

_COOLDOWN_PADRAO: dict[ErrorKind, float] = {
    ErrorKind.TIMEOUT: DEFAULT_COOLDOWN_TIMEOUT_S,
    ErrorKind.RATE_LIMIT: DEFAULT_COOLDOWN_RATE_LIMIT_S,
    ErrorKind.INVALID_RESPONSE: DEFAULT_COOLDOWN_INVALID_RESPONSE_S,
}


class Clock(Protocol):
    """Fonte de tempo monotonic usada pelos cooldowns."""

    def now(self) -> float:
        """Devolve o instante actual em segundos."""
        ...


class SystemClock:
    """Relógio monotonic do sistema."""

    def now(self) -> float:
        """Devolve o instante actual em segundos."""
        return monotonic()


class FakeClock:
    """Relógio determinístico para testes sem sleep real."""

    __slots__ = ("_agora",)

    def __init__(self, initial: float = 0.0) -> None:
        if isinstance(initial, bool) or not isinstance(initial, (int, float)):
            raise ValueError("initial tem de ser número.")
        if not math.isfinite(initial) or initial < 0:
            raise ValueError("initial tem de ser finito e não negativo.")
        self._agora = float(initial)

    def now(self) -> float:
        """Devolve o instante simulado."""
        return self._agora

    def advance(self, seconds: float) -> None:
        """Avança o relógio simulado."""
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise ValueError("seconds tem de ser número.")
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("seconds tem de ser finito e não negativo.")
        self._agora += float(seconds)


class CooldownTracker:
    """Regista janelas de cooldown por categoria de erro."""

    __slots__ = ("_clock", "_delays", "_ate")

    def __init__(
        self,
        clock: Clock | None = None,
        delays: Mapping[ErrorKind, float] | None = None,
    ) -> None:
        self._clock = clock if clock is not None else SystemClock()
        bruto = _COOLDOWN_PADRAO if delays is None else delays
        normalizado = {
            normalize_error_kind(kind): float(valor) for kind, valor in bruto.items()
        }
        if any(not math.isfinite(valor) or valor <= 0 for valor in normalizado.values()):
            raise ValueError("delays tem de conter valores finitos positivos.")
        self._delays = normalizado
        self._ate: dict[ErrorKind, float] = {}

    def activate(self, kind: TipoKind) -> None:
        """Activa o cooldown da categoria."""
        tipo = normalize_error_kind(kind)
        self._ate[tipo] = self._clock.now() + self._delays[tipo]

    def remaining(self, kind: TipoKind) -> float:
        """Devolve o tempo restante, zero quando não há cooldown."""
        tipo = normalize_error_kind(kind)
        return max(0.0, self._ate.get(tipo, 0.0) - self._clock.now())

    def is_active(self, kind: TipoKind) -> bool:
        """Indica se a categoria está em cooldown."""
        return self.remaining(kind) > 0.0

    def clear(self, kind: TipoKind) -> None:
        """Remove o cooldown da categoria."""
        self._ate.pop(normalize_error_kind(kind), None)
