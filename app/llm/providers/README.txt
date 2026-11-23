MÓDULO: llm.providers

FINALIDADE: Adaptadores finos para Gemini texto, Ollama e sessão live, usando apenas os contratos do gateway e a política de egress; nenhum SDK externo é importado.

FUNCIONALIDADES: ModelProvider como porta comum; transporte HTTP por urllib através de EgressPolicy; redacção de corpo e cabeçalhos antes da rede; timeout obrigatório por pedido; conversão de falhas HTTP, rede e timeout em ProviderError; Ollama em POST /api/generate com modelo de configuração; LiveSession como Protocol; criação de sessão real protegida por consentimento e aprovação de dependência.

ESTRUTURA:
- __init__.py — API pública.
- common.py — porta comum, validação de endpoint, transporte e normalização de resposta.
- gemini_text.py — adaptador de texto Gemini.
- ollama.py — adaptador Ollama.
- gemini_live.py — Protocol de voz e fábrica protegida.
- README.txt — esta descrição.
- module.yaml — metadados para as guardas.

INTERFACE PÚBLICA: GeminiTextProvider, OllamaProvider, LiveSession, LiveSessionUnavailable, ModelProvider, create_live_session.

DEPENDÊNCIAS: internas — app.core.config.SecretStr, app.llm.contracts, app.llm.egress; externas — dataclasses, http.client implícito em urllib, json, threading, time e typing da stdlib.

CONFIGURAÇÃO: o endpoint completo e a chave são fornecidos pelo chamador; nenhum endereço é inventado no código. O modelo Ollama vem de `HCW_OLLAMA_MODEL` via `load_settings()` e é validado por `validate_ollama_model`. O corpo enviado contém apenas `model`, `prompt` e `stream=false`; `task_id` e `correlation_id` ficam em eventos e logs. A resposta normalizada contém `text` e `tokens_used` opcional.

UTILIZAÇÃO:
adaptador = OllamaProvider(endpoint, EgressPolicy(), model=settings.ollama_model or "")
resposta = adaptador.complete(pedido)

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_config.py tests/unit/test_providers.py tests/integration/test_llm_ping.py tests/integration/test_llm_real.py

LIMITAÇÕES: o Ollama usa `POST /api/generate` e rejeita NDJSON/`done:false`; a sessão live real não é criada enquanto não houver dependência de voz aprovada; os testes reais só correm com `HCW_GEMINI_TEXT_ENDPOINT` ou `HCW_OLLAMA_ENDPOINT` e modelo real fornecido pelo Utilizador.

RELAÇÕES: usa core/config, llm.contracts, llm.egress e llm.router; é usado pelo CLI e pelo gateway de Fase 2.
