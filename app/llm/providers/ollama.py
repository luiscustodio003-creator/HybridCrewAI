"""Adaptador Ollama sobre o contrato comum, sem SDK externo."""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace

from app.core.config import validate_ollama_model
from app.llm.contracts import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)
from app.llm.egress import CloudConsent, EgressPolicy
from app.llm.providers.common import (
    ContextoEnvio,
    corpo_pedido,
    post_json,
    resposta_modelo,
    validar_adaptador,
    validar_endpoint,
)

_CAMINHO_GERAR = "/api/generate"


def _erro_resposta(provider: ProviderKind, request: ModelRequest, message: str) -> ProviderError:
    """Constrói um erro de resposta sem expor o conteúdo recebido."""
    return ProviderError(
        provider,
        ErrorKind.INVALID_RESPONSE,
        message,
        request.task_id,
        request.correlation_id,
    )


@dataclass(frozen=True)
class OllamaProvider:
    """Envia pedidos para o endpoint /api/generate do Ollama local."""

    endpoint: str
    egress: EgressPolicy
    consent: CloudConsent | None = None
    model: str = ""
    provider: ProviderKind = field(init=False, default=ProviderKind.OLLAMA)

    def __post_init__(self) -> None:
        validar_endpoint(self.endpoint)
        object.__setattr__(self, "model", validate_ollama_model(self.model))

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Executa o pedido e normaliza a resposta não streaming."""
        validar_adaptador(self.provider, request)
        inicio = time.perf_counter()
        dados = post_json(
            self.egress,
            f"{self.endpoint.rstrip('/')}{_CAMINHO_GERAR}",
            {},
            corpo_pedido(self.model, request.prompt),
            ContextoEnvio(request, self.consent),
        )
        concluido = dados.get("done")
        if concluido is False:
            raise _erro_resposta(
                self.provider,
                request,
                "Resposta de streaming não é aceite como resposta única.",
            )
        if concluido is not True:
            raise _erro_resposta(
                self.provider,
                request,
                "Resposta sem marcação done=true.",
            )
        corpo = {"text": dados.get("response"), "tokens_used": dados.get("eval_count")}
        return resposta_modelo(self.provider, replace(request, model=self.model), corpo, inicio)
