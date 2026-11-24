MÓDULO: llm

FINALIDADE: Definir os contratos, o consentimento cloud, a política de egress, o orçamento, a resiliência, a escada de fallback e a observabilidade redigida do gateway de modelos, sem expor tipos de SDK externo.

FUNCIONALIDADES: Modelos de pedido, resposta e erro; validação de timeout; redacção de segredos; consentimento persistido sem credenciais; recusa de cloud sem autorização; estimativa de tokens; limites por pedido e tarefa; selecção curta de ferramentas; retries limitados e cooldown por tipo de erro; escada de modelos carregada de JSON com matriz Gemini/Ollama/outro cloud; registo JSONL por chamada com provider, modelo, latência, tokens, task_id, correlation_id e pré-visualização redigida.

ESTRUTURA:
- __init__.py — API pública do módulo.
- contracts.py — contratos, enumerações e validações.
- observability.py — destino JSONL, redacção da pré-visualização, registo e consulta de chamadas.
- consent.py — consentimento cloud e tipo de conta Gemini em SQLite.
- egress/ — redacção, autorização e delimitação de conteúdo não confiável.
- prompts/ — prompts versionados e renderização segura.
- budget/ — orçamento de tokens e ferramentas.
- router/ — classificação de erros, retries, cooldowns e escada de fallback.
- providers/ — adaptadores HTTP e porta de sessão live sem SDK externo.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas do projecto.

INTERFACE PÚBLICA: ProviderKind, ErrorKind, ModelRequest, ModelResponse, ProviderError, AccountType, CloudConsentStore, EgressPolicy, PromptRegistry, PromptRecord, BudgetExceeded, BudgetLimits, TokenBudget, ToolSpec, estimate_tokens, select_tools, configure_observability, registar_chamada, ler_chamadas, previsualizacao_prompt; em app.llm.router: classify_error, RetryPolicy, RetryDecision, CooldownTracker, FakeClock, Ladder, LadderStep, RouteStep, StepAction, TaskKind, load_ladder, plan_fallback; em app.llm.providers: GeminiTextProvider, OllamaProvider, LiveSession, LiveSessionUnavailable, ModelProvider, create_live_session.

DEPENDÊNCIAS: internas — app.core.events, app.core.logging.SecretRegistry; externas — sqlite3 e urllib da stdlib.

CONFIGURAÇÃO: CLOUD_CONSENT_DEFAULT, GEMINI_ACCOUNT_TYPE_DEFAULT, DEFAULT_MAX_TOKENS_PER_REQUEST, DEFAULT_MAX_TOKENS_PER_TASK, DEFAULT_MAX_TOOLS_PER_REQUEST, DEFAULT_MAX_TOOL_DESCRIPTION_CHARS, DEFAULT_MAX_RETRY_ATTEMPTS, DEFAULT_RETRY_JITTER_FRACTION e os três DEFAULT_COOLDOWN_* em app.core.config.defaults; o timeout é obrigatório em cada pedido.

UTILIZAÇÃO:
from app.llm import ModelRequest, ProviderKind
pedido = ModelRequest(provider=ProviderKind.FAKE, model="fake-1", prompt="Diz olá", timeout_s=5.0, task_id="HCW-02-003", correlation_id="corr-1")

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_llm_contracts.py tests/unit/test_llm_consent.py tests/unit/test_llm_budget.py tests/unit/test_prompt_registry.py tests/unit/test_router_cooldown.py tests/unit/test_ladder.py tests/unit/test_providers.py tests/unit/test_llm_observability.py tests/integration/test_llm_real.py tests/security/test_egress.py

LIMITAÇÕES: não contacta fornecedores reais por omissão; a estimativa de tokens é determinística mas aproximada e os contadores não persistem entre processos; a política de retries não executa chamadas nem dorme; a escada aplica política; os adaptadores usam o formato interno do gateway e a sessão live real depende de biblioteca ainda não aprovada; o destino do JSONL é global por processo e a pré-visualização é truncada, sem recuperação do prompt completo.

RELAÇÕES: usa `app/llm/providers/` para contactar modelos, app.core.events e app.core.logging; o servidor em app/ui/server configura o destino do JSONL e expõe as chamadas registadas.
