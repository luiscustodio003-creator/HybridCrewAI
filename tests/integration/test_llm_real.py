"""Testes reais opcionais; por omissão não contactam fornecedores."""

from __future__ import annotations

import os

import pytest

from app.core.config import SecretStr
from app.llm.contracts import ModelRequest, ProviderKind
from app.llm.egress import EgressPolicy
from app.llm.providers import GeminiTextProvider, OllamaProvider

GEMINI_ENDPOINT = os.environ.get("HCW_GEMINI_TEXT_ENDPOINT")
GEMINI_MODEL = os.environ.get("HCW_LLM_REAL_MODEL")
OLLAMA_ENDPOINT = os.environ.get("HCW_OLLAMA_ENDPOINT")
OLLAMA_MODEL = os.environ.get("HCW_OLLAMA_MODEL")


class ConsentimentoReal:
    """Consentimento explícito apenas dentro deste teste."""

    def allows_cloud(self) -> bool:
        """Autoriza o pedido deste teste."""
        return True


def _pedido(provider: ProviderKind, model: str) -> ModelRequest:
    return ModelRequest(
        provider=provider,
        model=model,
        prompt="Responde apenas com uma palavra.",
        timeout_s=900.0,
        task_id="HCW-02-010-real",
        correlation_id="corr-real-opcional",
    )


@pytest.mark.skipif(
    not (GEMINI_ENDPOINT and GEMINI_MODEL),
    reason="HCW_GEMINI_TEXT_ENDPOINT e HCW_LLM_REAL_MODEL não configurados",
)
def test_gemini_text_real_opcional() -> None:
    assert GEMINI_ENDPOINT is not None
    assert GEMINI_MODEL is not None
    chave = os.environ.get("GEMINI_API_KEY")
    adaptador = GeminiTextProvider(
        GEMINI_ENDPOINT,
        EgressPolicy(allow_cloud=True),
        api_key=SecretStr(chave) if chave else None,
        consent=ConsentimentoReal(),
    )
    resposta = adaptador.complete(_pedido(ProviderKind.GEMINI_TEXT, GEMINI_MODEL))
    assert resposta.text
    assert resposta.provider is ProviderKind.GEMINI_TEXT


@pytest.mark.skipif(
    not (OLLAMA_ENDPOINT and OLLAMA_MODEL),
    reason="HCW_OLLAMA_ENDPOINT e HCW_OLLAMA_MODEL não configurados",
)
def test_ollama_real_opcional() -> None:
    assert OLLAMA_ENDPOINT is not None
    assert OLLAMA_MODEL is not None
    adaptador = OllamaProvider(
        OLLAMA_ENDPOINT,
        EgressPolicy(),
        model=OLLAMA_MODEL,
    )
    resposta = adaptador.complete(_pedido(ProviderKind.OLLAMA, OLLAMA_MODEL))
    assert resposta.text
    assert resposta.provider is ProviderKind.OLLAMA
