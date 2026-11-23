"""Adaptador de texto Gemini sobre o contrato comum, sem SDK externo."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.config import SecretStr
from app.llm.contracts import ModelRequest, ModelResponse, ProviderKind
from app.llm.egress import CloudConsent, EgressPolicy
from app.llm.providers.common import (
    ContextoEnvio,
    corpo_pedido,
    post_json,
    resposta_modelo,
    validar_adaptador,
    validar_endpoint,
)


@dataclass(frozen=True)
class GeminiTextProvider:
    """Envia pedidos de texto para um endpoint Gemini configurado."""

    endpoint: str
    egress: EgressPolicy
    api_key: SecretStr | None = None
    consent: CloudConsent | None = None
    provider: ProviderKind = field(init=False, default=ProviderKind.GEMINI_TEXT)

    def __post_init__(self) -> None:
        validar_endpoint(self.endpoint)

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Executa o pedido e normaliza a resposta."""
        validar_adaptador(self.provider, request)
        cabecalhos: dict[str, str] = {}
        if self.api_key is not None:
            cabecalhos["Authorization"] = f"Bearer {self.api_key.reveal()}"
        inicio = time.perf_counter()
        dados = post_json(
            self.egress,
            self.endpoint,
            cabecalhos,
            corpo_pedido(request),
            ContextoEnvio(request, self.consent),
        )
        return resposta_modelo(self.provider, request, dados, inicio)
