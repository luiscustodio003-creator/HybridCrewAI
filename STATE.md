# Estado do projecto
Fase actual: 2 · Gate: pendente (7/13 validadas)
Última tarefa validada: HCW-02-007 (2026-11-22) — orçamento de tokens/ferramentas em `app/llm/budget/`, evidência em `docs/reports/hcw-02-007.md`.
A meio: `HCW-02-008` a `HCW-02-012` estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-008`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-008` — classificar timeout, HTTP 429 e resposta inválida em `app/llm/router/errors.py`, com retries limitados, cooldown injetável por relógio falso e `tests/unit/test_router_cooldown.py`; sem sleep real nem fornecedores.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em `HCW-02-005`. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
