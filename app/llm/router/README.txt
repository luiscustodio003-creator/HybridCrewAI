MÓDULO: llm.router

FINALIDADE: Classificar falhas, limitar retries, controlar cooldowns por tipo de erro e aplicar a escada de modelos com matriz de fallback.

FUNCIONALIDADES: Classificação estável de timeout, HTTP 429, resposta inválida e rede; política de retries com jitter opcional; cooldowns distintos por categoria; relógio falso para testes sem sleep real; escada carregada de JSON; Gemini para Gemini automático; outro cloud só com autorização explícita; Ollama apenas em tarefa leve.

ESTRUTURA:
- __init__.py — API pública.
- errors.py — classificação, decisão de retry e atrasos.
- cooldown.py — janelas de cooldown e relógios.
- ladder.py — escada JSON e matriz de fallback.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: Clock, CooldownTracker, FakeClock, RetryDecision, RetryPolicy, SystemClock, classify_error, normalize_error_kind, Ladder, LadderError, LadderStep, RouteStep, StepAction, TaskKind, load_ladder, plan_fallback.

DEPENDÊNCIAS: internas — app.core.config.defaults, app.llm; externas — json, random e time da stdlib.

CONFIGURAÇÃO: DEFAULT_MAX_RETRY_ATTEMPTS, DEFAULT_RETRY_JITTER_FRACTION, DEFAULT_COOLDOWN_TIMEOUT_S, DEFAULT_COOLDOWN_RATE_LIMIT_S e DEFAULT_COOLDOWN_INVALID_RESPONSE_S em app.core.config.defaults. A escada vem de um ficheiro JSON com `version: 1` e `ladders.light`/`ladders.code`; cada degrau tem `provider` e `model`.

UTILIZAÇÃO:
decisao = RetryPolicy().decide(kind, attempt=1, jitter=False)
escada = load_ladder("config/llm_ladder.json")
rotas = plan_fallback(escada, TaskKind.LIGHT)

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_router_cooldown.py tests/unit/test_ladder.py

LIMITAÇÕES: a política não executa chamadas nem dorme; a escada não contacta fornecedores nem verifica consentimento — essas responsabilidades pertencem a egress, consentimento e adaptadores. EXTERNAL é uma classificação de política, não um fornecedor implementado.

RELAÇÕES: fornece decisões aos planeados adaptadores e CLI; reutiliza ProviderKind e ErrorKind de app.llm.
