"""Demonstração segura do gateway de modelos através da CLI."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.config import SecretStr, Settings, load_settings
from app.llm.consent import CloudConsentStore
from app.llm.contracts import ModelRequest, ModelResponse, ProviderError, ProviderKind
from app.llm.egress import CloudConsent, CloudDenied, EgressPolicy, redact_text
from app.llm.providers import GeminiTextProvider, OllamaProvider

_FALHA = 1
_TAREFA = "HCW-02-011"
_ENV_GEMINI = "GEMINI_API_KEY"


@dataclass(frozen=True, slots=True)
class ParametrosPing:
    """Parâmetros já validados pelo parser da CLI."""

    provider: str
    endpoint: str | None
    model: str
    prompt: str
    timeout_s: float
    allow_cloud: bool
    base_dir: Path | None
    api_key_env: str


@dataclass(frozen=True)
class SimulatedProvider:
    """Fornecedor simulado que nunca abre um socket."""

    provider: ProviderKind = ProviderKind.FAKE

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Devolve uma resposta local normalizada."""
        inicio = time.perf_counter()
        texto = f"pong simulado: {request.prompt}"
        return ModelResponse(
            provider=self.provider,
            model=request.model,
            text=texto,
            task_id=request.task_id,
            correlation_id=request.correlation_id,
            latency_ms=max(0.01, (time.perf_counter() - inicio) * 1000),
        )


TipoProvider = SimulatedProvider | OllamaProvider | GeminiTextProvider


def _consentimento(settings: Settings, allow_cloud: bool) -> CloudConsent | None:
    if not allow_cloud:
        return None
    return CloudConsentStore(settings.sqlite_path)


def _construir_provider(parametros: ParametrosPing) -> TipoProvider:
    if parametros.provider == "simulado":
        return SimulatedProvider()
    if parametros.endpoint is None:
        raise ValueError(
            f"--endpoint é obrigatório para o fornecedor {parametros.provider}."
        )
    settings = load_settings(None, parametros.base_dir)
    egress = EgressPolicy(allow_cloud=parametros.allow_cloud)
    consentimento = _consentimento(settings, parametros.allow_cloud)
    if parametros.provider == "ollama":
        return OllamaProvider(
            parametros.endpoint,
            egress,
            consentimento,
            model=settings.ollama_model or "",
        )
    chave = os.environ.get(parametros.api_key_env, "").strip()
    api_key = SecretStr(chave) if chave else None
    return GeminiTextProvider(
        parametros.endpoint,
        egress,
        api_key=api_key,
        consent=consentimento,
    )


def _pedido(provider: ProviderKind, parametros: ParametrosPing) -> ModelRequest:
    return ModelRequest(
        provider=provider,
        model=parametros.model,
        prompt=redact_text(parametros.prompt),
        timeout_s=parametros.timeout_s,
        task_id=_TAREFA,
        correlation_id=f"llm-ping-{uuid4().hex[:8]}",
    )


def _mostrar(resposta: ModelResponse, prompt: str) -> None:
    print(f"fornecedor: {resposta.provider.value}")
    print(f"modelo: {resposta.model}")
    print(f"latencia_ms: {resposta.latency_ms:.2f}")
    print(f"pre_visualizacao_pedido: {redact_text(prompt)}")
    print(f"pre_visualizacao_resposta: {redact_text(resposta.text)}")


def run(parametros: ParametrosPing) -> int:
    """Executa o ping e devolve zero apenas quando há resposta válida."""
    try:
        provider = _construir_provider(parametros)
        resposta = provider.complete(_pedido(provider.provider, parametros))
    except (ProviderError, CloudDenied, OSError, ValueError) as erro:
        print(f"llm ping FAIL: {redact_text(str(erro))}", file=sys.stderr)
        return _FALHA
    _mostrar(resposta, parametros.prompt)
    return 0
