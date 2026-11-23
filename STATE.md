# Estado do projecto
Fase actual: 2 · Gate: pendente (10/13 validadas)
Última tarefa validada: HCW-02-010 (2026-11-22) — adaptadores Gemini texto, Ollama e `LiveSession` em `app/llm/providers/`, evidência em `docs/reports/hcw-02-010.md`.
A meio: `HCW-02-011` e `HCW-02-012` estão `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para `HCW-02-011`; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-011` — criar `app/cli/llm_ping.py` e registar `hcw llm ping` em `app/cli/main.py`, com teste em `tests/integration/test_cli.py`, sem contactar fornecedores por omissão.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em `HCW-02-005`. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
