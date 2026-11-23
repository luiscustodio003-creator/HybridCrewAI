# Estado do projecto
Fase actual: 2 · Gate: pendente (11/13 validadas)
Última tarefa validada: HCW-02-011 (2026-11-23) — `hcw llm ping` em `app/cli/llm_ping.py`, registado em `app/cli/main.py`, evidência em `docs/reports/hcw-02-011.md`.
A meio: `HCW-02-012` está `APPROVED`. `HCW-00-006` continua `IMPLEMENTED` (5 erros de `ruff`, 3 de `mypy`).
Bloqueios: nenhum para o encerramento local de `HCW-02-011`; sem push sem aprovação explícita; nenhuma dependência de LLM/voz/rede foi instalada; etiquetas locais `phase-00-go` e `phase-01-go`;
 `ruff check .` global ainda falha por erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-02-012 — Consolidar segurança e evidências da Fase 2` com `hcw-implement`, `hcw-security-review` e `hcw-test-gate`.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em `HCW-02-005`. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
