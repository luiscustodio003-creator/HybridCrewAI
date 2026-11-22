"""Testes de logging central com correlação e redacção."""

from __future__ import annotations

from io import StringIO

import pytest

from app.core.config import SecretStr
from app.core.events import EventBus, EventContext, EventLevel
from app.core.logging import (
    EventLogger,
    LoggingContextError,
    SecretRegistry,
    bind_context,
    configure_logging,
    current_context,
    reset_context,
)

FAKE_KEY = "sk-TEST-LOG-NAO-APARECE"
NUM_LOGS = 2
CONTEXTO = EventContext(
    correlation_id="corr-log-1",
    task_id="HCW-01-005",
    agent="open-code",
    phase="1",
)


def criar_logger(
    stream: StringIO, segredos: SecretRegistry | None = None
) -> EventLogger:
    """Cria um logger com destino em memória."""
    return configure_logging(
        EventBus(), stream=stream, secrets=segredos or SecretRegistry()
    )


def test_segredo_nao_aparece_em_logs() -> None:
    stream = StringIO()
    registry = SecretRegistry([SecretStr(FAKE_KEY)])
    logger = criar_logger(stream, registry)
    token = bind_context(CONTEXTO)
    try:
        logger.info(f"a chave é {FAKE_KEY}")
    finally:
        reset_context(token)
    assert FAKE_KEY not in stream.getvalue()
    assert "***REDACTED***" in stream.getvalue()


def test_logs_da_tarefa_partilham_correlation_id() -> None:
    stream = StringIO()
    logger = criar_logger(stream)
    token = bind_context(CONTEXTO)
    try:
        primeiro = logger.info("início")
        segundo = logger.warning("aviso")
    finally:
        reset_context(token)
    assert primeiro.correlation_id == segundo.correlation_id == CONTEXTO.correlation_id
    assert stream.getvalue().count(CONTEXTO.correlation_id) == NUM_LOGS


def test_erro_inclui_stack_trace_e_phase() -> None:
    stream = StringIO()
    logger = criar_logger(stream)
    token = bind_context(CONTEXTO)
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            logger.error("falha", exc_info=True)
    finally:
        reset_context(token)
    saida = stream.getvalue()
    assert CONTEXTO.phase in saida
    assert "ValueError: boom" in saida
    assert "stack_trace" in saida


def test_sem_contexto_a_abortar() -> None:
    logger = criar_logger(StringIO())
    with pytest.raises(LoggingContextError, match="correlation_id"):
        logger.info("sem contexto")


def test_contexto_pode_ser_aninhado_e_reposto() -> None:
    primeiro = bind_context(CONTEXTO)
    outro = EventContext(
        correlation_id="corr-filha",
        task_id="HCW-01-005",
        agent="sub-agente",
        phase="1",
    )
    segundo = bind_context(outro)
    assert current_context() == outro
    reset_context(segundo)
    assert current_context() == CONTEXTO
    reset_context(primeiro)
    assert current_context() is None


def test_nivel_minimo_filtra_debug() -> None:
    logger = EventLogger(
        EventBus(), min_level=EventLevel.INFO, secrets=SecretRegistry()
    )
    token = bind_context(CONTEXTO)
    try:
        assert logger.debug("detalhe") is None
        assert logger.info("visível") is not None
    finally:
        reset_context(token)


def test_registo_redige_multiplos_segredos() -> None:
    registry = SecretRegistry([SecretStr("um"), SecretStr("dois")])
    assert registry.redact("um e dois") == "***REDACTED*** e ***REDACTED***"
