# Estado do projecto
Fase actual: 2 · Gate: pendente (5/13 validadas)
Última tarefa validada: HCW-02-005 (2026-11-22) — consentimento cloud e tipo de conta em `app/llm/consent.py`, evidência em `docs/reports/hcw-02-005.md`.
A meio: `HCW-02-006` a `HCW-02-012` estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-006`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-006` — criar registo de prompts versionados em `app/llm/prompt_registry.py` e `app/llm/prompt_store.py`, com `tests/unit/test_llm_prompts.py`; versionar prompts sem alterar comportamento; não instalar dependências.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em `HCW-02-005`, mas a escolha do utilizador continua pendente. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
