MÓDULO: core/logging
FINALIDADE: Centralizar registos com correlation_id, redacção de segredos e stack trace nos erros.
FUNCIONALIDADES: contexto de correlação por fluxo (contextvars); registo de segredos a redigir; emissão de eventos log.* para o EventBus; destino textual redigido; filtro por nível mínimo; captura de stack trace em erros.
ESTRUTURA: correlation.py (bind_context, reset_context, current_context); redaction.py (SecretRegistry); setup.py (EventLogger, TextLogSink, configure_logging); __init__.py (API pública).
INTERFACE PÚBLICA: EventLogger, configure_logging, TextLogSink, SecretRegistry, bind_context, reset_context, current_context, LoggingError, LoggingContextError.
DEPENDÊNCIAS: core/config (redact, SecretStr) e core/events (EventContext, EventBus, EventLevel, new_event); biblioteca padrão (contextvars, sys, traceback, typing).
CONFIGURAÇÃO: nível mínimo por omissão `info`; fluxo textual por omissão `sys.stderr`; segredos registados explicitamente.
UTILIZAÇÃO: registry = SecretRegistry([SecretStr(valor)]); logger = configure_logging(bus, secrets=registry); token = bind_context(EventContext(...)); logger.info("arranque"); reset_context(token).
TESTES: python -m pytest -q tests/unit/test_logging.py
LIMITAÇÕES: não usa o módulo `logging` da biblioteca padrão; não faz rotação de ficheiros; exige contexto associado antes de registar.
RELAÇÕES: usado por core/tasks, core/results, core/security, cli e camadas seguintes.
