# ADR-0002 — Gateway de modelos: contrato próprio e adaptadores finos

Estado: ACEITE
Data: 2026-11-22 · Aprovado pelo utilizador em 2026-11-22

## Contexto

A Fase 2 precisa de um único ponto de entrada para pedidos a modelos. Os requisitos `FR-005`, `FR-006` e `FR-007` pedem contratos estáveis, timeout obrigatório, escada de fallback e consentimento cloud explícito. `SEC-002` exige que segredos e conteúdo não confiável não saiam sem controlo. `NFR-005` exige prompts versionados e `OPS-005` exige observabilidade sem revelar credenciais.

A Fase 1 entregou `SecretStr`, `redact`, `SecretRegistry`, `Settings`, registo de eventos, SQLite e `ToolResult`. A ADR-0001 fixou o princípio de que o motor é próprio e que frameworks ficam atrás de portas estáveis. A auditoria de 2026-11-22 confirmou que o `.venv` tem apenas `pytest`, `ruff`, `mypy` e `PyYAML`: não há `httpx`, `requests`, `google-genai`, `litellm` nem `ollama` instalados. `docs/reports/baseline-freeze.txt` regista versões globais de referência, mas não autoriza instalação no ambiente do projecto.

Gemini Live é uma sessão de voz com estado, enquanto os pedidos de texto e o Ollama local são pedidos sem estado. O tipo de conta Gemini (P-05) ainda não foi decidido, pelo que `desconhecido` não pode autorizar tráfego externo.

## Problema

Escolher como integrar Gemini texto, Gemini Live e Ollama sem espalhar decisões de segurança por adaptadores, sem inventar APIs e sem criar uma dependência que o projecto ainda não pode verificar. A escolha tem de permitir testes com servidor HTTP falso em Windows e Linux, com documentação em português de Portugal e sem novas dependências.

## Alternativas

### LiteLLM

- **Prós:** uma API comum para vários fornecedores; menos código de adaptador; retries e mapeamento de erros parcialmente prontos.
- **Contras:** nova dependência não instalada nem auditada; superfície adicional entre a política de egress e a rede; versão e comportamento de retries teriam de ser confirmados na documentação oficial; a sessão de voz de baixa latência não fica naturalmente atrás do mesmo contrato de pedido/resposta; enfraquece o controlo explícito de timeout, redacção e consentimento exigido por `SEC-002`.
- **Evidência:** não foi executada nem medida; o ambiente actual não contém o pacote.

### SDK nativo directo em cada adaptador

- **Prós:** acesso mais directo a funcionalidades do fornecedor, incluindo Gemini Live; menos camadas entre chamada e serviço.
- **Contras:** tipos e erros do SDK espalham-se pelo código; cada adaptador teria de repetir timeout, redacção, consentimento e classificação de erro; testes exigem instalar vários SDKs; troca de fornecedor passa a tocar no núcleo; contrário a `NFR-003` e ao padrão da ADR-0001.
- **Evidência:** o ambiente não tem os SDKs; a ficha da Fase 2 pede explicitamente um gateway único.

### Contrato próprio com adaptadores finos

- **Prós:** nenhuma dependência nova na Fase 2; o mesmo `ModelRequest`/`ModelResponse` para todos os caminhos; egress, orçamento, cooldown e consentimento ficam antes da rede; testes com `http.server` e `urllib.request` da stdlib; alinhado com ADR-0001; diferentes tipos de voz
 ficam isolados atrás de `LiveSession`.
- **Contras:** mais código de adaptador e mais manutenção de contratos; funcionalidades avançadas de fornecedores ficam de fora até nova decisão; a integração real só é exercitada quando houver credenciais e endereços configurados.
- **Evidência:** Fase 1 já demonstrou que contratos próprios e SQLite funcionam com stdlib; 90 testes passam sem dependências de LLM.

## Decisão

Adoptar **contrato próprio com adaptadores finos** para a Fase 2, com estado `PROPOSTA` até aprovação do utilizador:

1. `app/llm/contracts.py` define `ModelRequest`, `ModelResponse` e `ProviderError`, imutáveis, tipados e com timeout positivo obrigatório.
2. Todos os adaptadores implementam uma porta comum e não exportam tipos de SDK externo. Não há `import litellm`, `google.genai` nem `ollama` no código da Fase 2.
3. O transporte inicial usa apenas `urllib.request` da stdlib. Endereços base, modelos e chaves vêm de configuração; nenhum endpoint é inventado no código.
4. `GeminiTextProvider` e `OllamaProvider` concretizam a porta para pedidos sem estado. A sessão de voz usa `LiveSession` como `Protocol` com operações de iniciar, enviar, receber e fechar; a implementação real só entra quando esta ADR for aceite e uma dependência for explicitamente aprovada.
5. Antes de qualquer socket, o pedido passa por egress, consentimento, orçamento e classificação de erro. Consentimento `desconhecido` equivale a negação.
6. Respostas e mensagens de erro nunca contêm segredos; a pré-visualização em eventos e na CLI é integralmente redigida.
7. LiteLLM ou SDKs nativos só podem ser introduzidos por nova ADR, com versão fixada, `pip-audit`, aprovação explícita e adaptador isolado.
8. Não é instalada nenhuma dependência de LLM, rede ou voz enquanto esta ADR não for aceite.

## Justificação

A escolha preserva a fronteira "o modelo propõe, o Python executa": a política permanece no código do projecto e não na biblioteca de terceiros. Também resolve o problema prático do ambiente actual — não há pacotes instalados — sem adiar a Fase 2 para uma decisão de instalação.

O contrato comum permite testar fallback, cooldown, timeout e redacção com servidores locais falsos, exactamente como o gate da Fase 2 exige. `LiveSession` como `Protocol` evita que tipos de voz vazem para o resto da aplicação e deixa a decisão P-05 separada da decisão de arquitectura.

## Consequências

- `HCW-02-003` a `HCW-02-011` implementam contra a porta comum; nenhuma tarefa instala dependências.
- Os adaptadores reais só são exercitados em `tests/integration/test_llm_real.py` quando configurados por ambiente; por omissão usam servidor falso.
- A matriz Gemini → Gemini, Gemini → Ollama e Gemini → outro cloud é configurável e testada sem chamadas externas.
- Funcionalidades específicas de Gemini Live ficam adiadas até aprovação desta ADR e de uma dependência de voz.
- Se testes com servidor falso mostrarem que `urllib.request` não cobre um caso necessário, a correcção volta a esta ADR; não se troca a biblioteca silenciosamente.

## Segurança

| Ameaça | Contramedida nesta decisão | Teste previsto |
|---|---|---|
| Fuga de segredos para a cloud (`SEC-002`) | Scan e redacção antes da porta de rede; `SecretStr` reutilizado | `tests/security/test_egress.py` com servidor falso e chave falsa |
| Injecção em conteúdo externo | Bloco delimitado por `untrusted_wrap.py`; marcador de fecho forjado rejeitado | `tests/security/test_egress.py` com instruções hostis |
| Custos e quotas fora de controlo | Orçamento e limite de ferramentas antes da chamada | `tests/unit/test_llm_budget.py` |
| Dependência comprometida | Nenhuma instalação nesta fase; versões fixadas só em nova ADR | Revisão do plano e do `pip freeze` na auditoria |
| Sessão de voz com tipo externo vazado | `LiveSession` como `Protocol` local | `tests/unit/test_providers.py` |
| Pedido cloud sem consentimento | Consentimento verificado antes do socket; `desconhecido` nega | `tests/unit/test_llm_consent.py` |

## Evidência

- `docs/phases/phase-02.md` — objectivos, matriz de fallback e limites da Fase 2.
- `docs/reports/phase-02-plan.md` — plano aprovado pelo utilizador em 2026-11-22.
- `docs/reports/audit.md` — inventário real do `.venv` e ausência de dependências de LLM.
- `docs/requirements.yaml` — `FR-005`, `FR-006`, `FR-007`, `SEC-002`, `NFR-005`, `OPS-005`.
- `docs/adr/ADR-0001-motor-de-agentes.md` — decisão de núcleo próprio com adaptadores futuros.
