"""Testes dos contratos base do gateway de modelos."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, is_dataclass

import pytest

import app
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
    with pytest.raises(FrozenInstanceError):
        pedido.prompt = "outro"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        resposta.text = "outro"  # type: ignore[misc]


def test_provider_error_atravessa_contextmanager() -> None:
    erro = ProviderError(
        provider=ProviderKind.FAKE,
        kind=ErrorKind.TIMEOUT,
        message="expirou",
        task_id="HCW-02-013",
        correlation_id="corr-ctx",
    )

    @contextmanager
    def lancar() -> Iterator[None]:
        raise erro
        yield

    with pytest.raises(ProviderError) as capturado:
        with lancar():
            pytest.fail("o contexto não devia continuar após a excepção")

    assert capturado.value is erro
    assert capturado.value.kind is ErrorKind.TIMEOUT
    assert capturado.value.message == "expirou"
    assert capturado.value.args == ("expirou",)


def test_outras_excecoes_nao_sao_dataclasses_frozen() -> None:
    problemas: list[str] = []
    for modulo in pkgutil.walk_packages(app.__path__, "app."):
        if modulo.name.endswith(".__main__"):
            continue
        carregado = importlib.import_module(modulo.name)
        for nome, cls in inspect.getmembers(carregado, inspect.isclass):
            if cls.__module__ != modulo.name:
                continue
            if not issubclass(cls, BaseException):
                continue
            if is_dataclass(cls) and cls.__dataclass_params__.frozen:
                problemas.append(f"{modulo.name}.{nome}")

    assert problemas == [], f"Excepções frozen encontradas: {problemas}"


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
    assert erro.provider is ProviderKind.OLLAMA
    assert erro.kind is ErrorKind.NETWORK
    assert erro.message == "sem ligação"
    assert erro.task_id == "HCW-02-003"
    assert erro.correlation_id == "corr-1"
    assert erro.retryable is True
    assert erro.args == ("sem ligação",)
