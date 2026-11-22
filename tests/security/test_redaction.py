"""Testes de redacção de segredos em logs."""

from __future__ import annotations

from io import StringIO

from app.core.config import SecretStr
from app.core.events import EventBus, EventContext
from app.core.logging import (
    SecretRegistry,
    bind_context,
    configure_logging,
    reset_context,
)

CONTEXTO = EventContext(
    correlation_id="corr-seg-1",
    task_id="HCW-01-005",
    agent="open-code",
    phase="1",
)
CHAVE_FALSA = "sk-TEST-SEGURANCA-NAO-APARECE"
VALOR = "abc123DEF456"


def test_padrao_sk_e_redigido() -> None:
    assert SecretRegistry().redact(f"chave {CHAVE_FALSA}") == "chave ***REDACTED***"


def test_nome_declarado_e_redigido() -> None:
    registry = SecretRegistry(names=["GEMINI_API_KEY"])
    assert (
        registry.redact(f"GEMINI_API_KEY={VALOR}")
        == "GEMINI_API_KEY=***REDACTED***"
    )


def test_nome_nao_declarado_nao_e_alterado() -> None:
    registry = SecretRegistry(names=["GEMINI_API_KEY"])
    assert registry.redact(f"OUTRA_VARIAVEL={VALOR}") == f"OUTRA_VARIAVEL={VALOR}"


def test_valor_exato_registado_e_redigido() -> None:
    registry = SecretRegistry([SecretStr("um"), SecretStr("dois")])
    assert registry.redact("um e dois") == "***REDACTED*** e ***REDACTED***"


def test_chave_falsa_nao_aparece_no_destino_textual() -> None:
    stream = StringIO()
    logger = configure_logging(EventBus(), stream=stream, secrets=SecretRegistry())
    token = bind_context(CONTEXTO)
    try:
        logger.info(f"ligar com {CHAVE_FALSA}")
    finally:
        reset_context(token)
    assert CHAVE_FALSA not in stream.getvalue()
    assert "***REDACTED***" in stream.getvalue()


def test_nome_invalido_e_recusado() -> None:
    try:
        SecretRegistry(names=["api key"])
    except ValueError as erro:
        assert "Nome de segredo inválido" in str(erro)
    else:
        raise AssertionError("Era esperado ValueError para nome inválido")
