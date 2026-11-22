# Plano aprovado da Fase 2 — LLM Gateway com política de egress

Data: 2026-11-22 · Gate: pendente · Plano: APROVADO pelo utilizador

## Objectivo

Uma única porta para os modelos, com controlo do que sai para a cloud. Gemini Live para conversa, modelos de texto Gemini para agentes e Ollama em segundo plano, sem instalar novas dependências nesta fase.

## Tarefas aprovadas

| ID | Título | Dependências | Teste principal |
|---|---|---|---|
| HCW-02-002 | Decidir a integração de modelos em ADR-0002 | HCW-02-001 | Revisão documental; sem teste de código |
| HCW-02-003 | Criar contratos e erros base do gateway | HCW-02-002 | `tests/unit/test_llm_contracts.py` |
| HCW-02-004 | Implementar política de egress e redacção de payload | HCW-02-003 | `tests/security/test_egress.py` |
| HCW-02-005 | Registar consentimento cloud e tipo de conta | HCW-02-004 | `tests/unit/test_llm_consent.py` |
| HCW-02-006 | Criar registo de prompts versionados | HCW-02-004 | `tests/unit/test_prompt_registry.py` |
| HCW-02-007 | Aplicar orçamento de tokens e de ferramentas | HCW-02-003 | `tests/unit/test_llm_budget.py` |
| HCW-02-008 | Classificar erros, retries e cooldown por tipo | HCW-02-003 | `tests/unit/test_router_cooldown.py` |
| HCW-02-009 | Implementar escada de modelos e matriz de fallback | HCW-02-005, -007, -008 | `tests/unit/test_ladder.py` |
| HCW-02-010 | Criar adaptadores Gemini Live, Gemini texto e Ollama | HCW-02-006, -007, -009 | `tests/unit/test_providers.py`, `tests/integration/test_llm_real.py` |
| HCW-02-011 | Adicionar comando `hcw llm ping` | HCW-02-010 | `tests/integration/test_llm_ping.py` |
| HCW-02-012 | Consolidar segurança e evidências da Fase 2 | HCW-02-004, -009, -011 | Revisão de `tests/security/test_egress.py` |
| HCW-02-999 | Gate da Fase 2 | Todas as anteriores | `python scripts/run_gate.py --phase 2` |

## Requisitos acrescentados

- `FR-005` — gateway único com contratos estáveis e timeout obrigatório.
- `FR-006` — escada configurável, retries limitados e cooldown por erro.
- `FR-007` — consentimento cloud explícito antes de qualquer pedido externo.
- `SEC-002` — payloads sem segredos e com conteúdo não confiável delimitado.
- `NFR-005` — prompts versionados e rastreáveis.
- `OPS-005` — pedidos observáveis com fornecedor, latência e pré-visualização redigida.

## Verificações do plano

- `python scripts/validate_plan.py` → 0 erros, 0 avisos.
- `python scripts/check_traceability.py` → 0 erros, 0 avisos.
- `python scripts/check_file_size.py` → 0 erros, 0 avisos.
- `python scripts/check_modules.py` → 0 erros, 0 avisos.
- `python scripts/plan_status.py` → Fase 02 `0/13`, próxima `HCW-02-001`.
- `.venv\Scripts\python.exe -m pytest -q` → 90 testes passam.

## Decisões e paragens

- ADR-0002 será escrito em `HCW-02-002` com estado `PROPOSTA`. Só o utilizador o passa a `ACEITE`.
- Não serão instalados `httpx`, `requests`, `google-genai`, `litellm` nem `ollama` sem aprovação explícita.
- Integrações reais com Gemini e Ollama ficam opcionais, controladas por configuração e consentimento.
- O tipo de conta Gemini (P-05) continua por decidir; `desconhecido` nunca autoriza cloud.

## Limitações conhecidas

- Ainda não existe `app/llm/`; todas as pastas e contratos são propostos neste plano.
- `ruff check .` e `mypy scripts` continuam com erros pré-existentes em `scripts/` (`HCW-00-006`).
- A auditoria incremental está em `docs/reports/audit.md`; nenhum pedido real a fornecedor foi executado.
