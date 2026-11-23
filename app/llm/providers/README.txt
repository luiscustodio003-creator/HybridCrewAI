MÓDULO: llm.providers

FINALIDADE: Adaptadores finos para Gemini texto, Ollama e sessão live, usando apenas os contratos do gateway e a política de egress; nenhum SDK externo é importado.

FUNCIONALIDADES: ModelProvider como porta comum; transporte HTTP por urllib através de EgressPolicy; redacção de corpo e cabeçalhos antes da rede; timeout obrigatório por pedido; conversão de falhas HTTP, rede e timeout em ProviderError; LiveSession como Protocol; criação de sessão real protegida por consentimento e aprovação de dependência.

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

CONFIGURAÇÃO: o endpoint completo, o modelo e a chave são fornecidos pelo chamador; nenhum endereço é inventado no código. O corpo interno do gateway contém `model`, `prompt`, `task_id` e `correlation_id`; a resposta esperada contém `text` e `tokens_used` opcional.

UTILIZAÇÃO:
adaptador = GeminiTextProvider(endpoint, EgressPolicy(), api_key=SecretStr(chave), consent=consentimento)
resposta = adaptador.complete(pedido)

TESTES: .venv\Scripts\python.exe -m pytest -q tests/unit/test_providers.py tests/integration/test_llm_real.py

LIMITAÇÕES: o formato de fio é o contrato interno do gateway, não uma emulação de API externa; a sessão live real não é criada enquanto não houver dependência de voz aprovada; os testes reais só correm com HCW_GEMINI_TEXT_ENDPOINT ou HCW_OLLAMA_ENDPOINT no ambiente.

RELAÇÕES: usa llm.contracts, llm.egress e llm.router; será usado pelo CLI e pelo gateway de Fase 2.
