"""Testes reais opcionais; por omissão não contactam fornecedores."""

from __future__ import annotations

import os

import pytest

from app.core.config import SecretStr
from app.llm.contracts import ModelRequest, ProviderKind
from app.llm.egress import EgressPolicy
from app.llm.providers import GeminiTextProvider, OllamaProvider

GEMINI_ENDPOINT = os.environ.get("HCW_GEMINI_TEXT_ENDPOINT")
OLLAMA_ENDPOINT = os.environ.get("HCW_OLLAMA_ENDPOINT")


class ConsentimentoReal:
    """Consentimento explícito apenas dentro deste teste."""

    def allows_cloud(self) -> bool:
        """Autoriza o pedido deste teste."""
        return True


def _pedido(provider: ProviderKind) -> ModelRequest:
    return ModelRequest(
        provider=provider,
        model=os.environ.get("HCW_LLM_REAL_MODEL", "modelo-configurado"),
        prompt="Responde apenas com uma palavra.",
        timeout_s=5.0,
        task_id="HCW-02-010-real",
        correlation_id="corr-real-opcional",
    )


@pytest.mark.skipif(not GEMINI_ENDPOINT, reason="HCW_GEMINI_TEXT_ENDPOINT não configurado")
def test_gemini_text_real_opcional() -> None:
    chave = os.environ.get("GEMINI_API_KEY")
    adaptador = GeminiTextProvider(
        GEMINI_ENDPOINT or "",
        EgressPolicy(allow_cloud=True),
        api_key=SecretStr(chave) if chave else None,
        consent=ConsentimentoReal(),
    )
    resposta = adaptador.complete(_pedido(ProviderKind.GEMINI_TEXT))
    assert resposta.text
    assert resposta.provider is ProviderKind.GEMINI_TEXT


@pytest.mark.skipif(not OLLAMA_ENDPOINT, reason="HCW_OLLAMA_ENDPOINT não configurado")
def test_ollama_real_opcional() -> None:
    adaptador = OllamaProvider(
        OLLAMA_ENDPOINT or "",
        EgressPolicy(),
    )
    resposta = adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert resposta.text
    assert resposta.provider is ProviderKind.OLLAMA
