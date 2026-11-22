MÓDULO: llm.router

FINALIDADE: Classificar falhas de fornecedor, limitar retries e controlar cooldowns por tipo de erro.

FUNCIONALIDADES: Classificação estável de timeout, HTTP 429, resposta inválida e rede; política de retries com jitter opcional; cooldowns distintos por categoria; relógio falso para testes sem sleep real.

ESTRUTURA:
- __init__.py — API pública.
- errors.py — classificação, decisão de retry e atrasos.
- cooldown.py — janelas de cooldown e relógios.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: Clock, CooldownTracker, FakeClock, RetryDecision, RetryPolicy, SystemClock, classify_error, normalize_error_kind.

DEPENDÊNCIAS: internas — app.core.config.defaults, app.llm; externas — random e time da stdlib.

CONFIGURAÇÃO: DEFAULT_MAX_RETRY_ATTEMPTS, DEFAULT_RETRY_JITTER_FRACTION, DEFAULT_COOLDOWN_TIMEOUT_S, DEFAULT_COOLDOWN_RATE_LIMIT_S e DEFAULT_COOLDOWN_INVALID_RESPONSE_S em app.core.config.defaults.

UTILIZAÇÃO:
decisao = RetryPolicy().decide(kind, attempt=1, jitter=False)
cooldowns = CooldownTracker(FakeClock())
cooldowns.activate(kind)

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_router_cooldown.py

LIMITAÇÕES: a política não executa chamadas nem dorme; o roteador ainda não escolhe modelos nem faz fallback.

RELAÇÕES: usado pelo planeado roteador de escada e providers; reutiliza ErrorKind de app.llm.
