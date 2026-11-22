"""Testes dos contratos base do gateway de modelos."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.llm import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)

FRASE_SECRETA = "sk-abc123XYZ GEMINI_API_KEY=super-secreto AKIA1234567890ABCDEF"


def _pedido(**alteracoes: object) -> ModelRequest:
    dados: dict[str, object] = {
        "provider": ProviderKind.FAKE,
        "model": "fake-1",
        "prompt": "Diz olá",
        "timeout_s": 5.0,
        "task_id": "HCW-02-003",
        "correlation_id": "corr-1",
    }
    dados.update(alteracoes)
    return ModelRequest(**dados)  # type: ignore[arg-type]


def test_modelos_sao_imutaveis() -> None:
    pedido = _pedido()
    resposta = ModelResponse(
        provider=ProviderKind.FAKE,
        model="fake-1",
        text="olá",
        task_id="HCW-02-003",
        correlation_id="corr-1",
        latency_ms=12.5,
    )
    erro = ProviderError(
        provider=ProviderKind.FAKE,
        kind=ErrorKind.TIMEOUT,
        message="expirou",
        task_id="HCW-02-003",
        correlation_id="corr-1",
    )
    with pytest.raises(FrozenInstanceError):
        pedido.prompt = "outro"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        resposta.text = "outro"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        erro.message = "outro"  # type: ignore[misc]


def test_provider_tem_de_ser_tipo_explicito() -> None:
    with pytest.raises(TypeError):
        _pedido(provider="fake")


@pytest.mark.parametrize("valor", [None, 0, -1, float("nan"), float("inf"), True])
def test_timeout_tem_de_ser_positivo_e_finito(valor: object) -> None:
    with pytest.raises(ValueError):
        _pedido(timeout_s=valor)


def test_repr_dos_modelos_nunca_revela_segredos() -> None:
    pedido = _pedido(prompt=FRASE_SECRETA)
    resposta = ModelResponse(
        provider=ProviderKind.GEMINI_TEXT,
        model="gemini-2.5-flash",
        text=FRASE_SECRETA,
        task_id="HCW-02-003",
        correlation_id="corr-1",
        latency_ms=12.5,
    )
    erro = ProviderError(
        provider=ProviderKind.GEMINI_LIVE,
        kind=ErrorKind.AUTH,
        message=FRASE_SECRETA,
        task_id="HCW-02-003",
        correlation_id="corr-1",
    )
    for texto in (repr(pedido), repr(resposta), repr(erro), str(erro)):
        assert "sk-abc123XYZ" not in texto
        assert "super-secreto" not in texto
        assert "AKIA1234567890ABCDEF" not in texto
        assert "***REDACTED***" in texto


def test_erro_e_uma_excecao_com_codigo_explicito() -> None:
    erro = ProviderError(
        provider=ProviderKind.OLLAMA,
        kind=ErrorKind.NETWORK,
        message="sem ligação",
        task_id="HCW-02-003",
        correlation_id="corr-1",
        retryable=True,
    )
    assert isinstance(erro, Exception)
    assert erro.kind is ErrorKind.NETWORK
    assert erro.retryable is True
