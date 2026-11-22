MÓDULO: llm.budget

FINALIDADE: Impedir pedidos caros e listas de ferramentas grandes antes de contactar um fornecedor.

FUNCIONALIDADES: Estimativa determinística de tokens; limites por pedido e por tarefa; erro tipado `BudgetExceeded`; evento `budget.exceeded`; selecção curta de ferramentas com descrições truncadas.

ESTRUTURA:
- __init__.py — API pública.
- tokens.py — limites, estimativa e reserva.
- tools_budget.py — ferramentas para Ollama.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: BudgetExceeded, BudgetLimits, TokenBudget, ToolSpec, estimate_tokens, select_tools.

DEPENDÊNCIAS: internas — app.core.config.defaults, app.core.events; externas — nenhuma.

CONFIGURAÇÃO: limites por omissão em `app.core.config.defaults` e injectados por `BudgetLimits`.

UTILIZAÇÃO:
orcamento = TokenBudget(BudgetLimits(), bus, contexto)
orcamento.reserve(texto)
ferramentas = select_tools(catalogo, limites.max_tools, limites.max_tool_description_chars)

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_llm_budget.py

LIMITAÇÕES: a estimativa é aproximada e não substitui contadores oficiais; não faz chamadas de rede; não persisted contadores entre processos.

RELAÇÕES: usado pelo roteador e pelos providers; publica eventos no barramento central.
