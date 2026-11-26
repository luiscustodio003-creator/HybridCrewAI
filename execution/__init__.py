"""API pública do executor simples não isolado."""

from execution.guard import GUARDA_SUBPROCESSO, ambiente_limpo
from execution.models import (
    TIMEOUT_MAXIMO_S,
    TIMEOUT_PADRAO_S,
    ExecutionConfigError,
    ExecutionRequest,
    ExecutionResult,
)
from execution.simple_runner import SimpleRunner

__all__ = [
    "GUARDA_SUBPROCESSO",
    "TIMEOUT_MAXIMO_S",
    "TIMEOUT_PADRAO_S",
    "ExecutionConfigError",
    "ExecutionRequest",
    "ExecutionResult",
    "SimpleRunner",
    "ambiente_limpo",
]
