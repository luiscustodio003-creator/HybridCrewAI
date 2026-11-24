"""API pública do gateway de modelos."""

from app.llm.contracts import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)
from app.llm.observability import (
    configure_observability,
    ler_chamadas,
    previsualizacao_prompt,
    registar_chamada,
)

__all__ = [
    "ErrorKind",
    "ModelRequest",
    "ModelResponse",
    "ProviderError",
    "ProviderKind",
    "configure_observability",
    "ler_chamadas",
    "previsualizacao_prompt",
    "registar_chamada",
]
