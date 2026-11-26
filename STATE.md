# Estado do projecto
Fase actual: 4 · Gate: **GO** em 2026-11-26T16:39:38 (`reports/phase-04/report.md`); `HCW-04-999` validada e etiqueta `phase-04-go` criada em `cb230cb` sem `--force`.
Última tarefa validada: HCW-04-999 (2026-11-26) — gate da Fase 4 com validadores OK e pytest cumulativo OK em 51 ficheiros; evidência em `reports/phase-04/report.md` e `refs/tags/phase-04-go`.
A meio: `HCW-04-001` a `HCW-04-014` validadas; HCW-04-013 tornou o filtro LLM determinístico e HCW-04-014 eliminou o `ConnectionAbortedError` cumulativo com drenagem limitada do corpo de POST recusado.
Bloqueios: nenhum bloqueio de Git; commit e push da Fase 4 executados com autorização explícita. A etiqueta `phase-04-go` continua em `cb230cb`, enquanto o commit da Fase 4 fica depois dela. `screenshots/phase-03/01-eventos.png`, `02-chat.png` e `screenshots/phase-04/02-aprovacao.png` foram preservados fora do commit. HCW-00-006 continua IMPLEMENTED (5 erros de ruff, 3 de mypy); `ruff check .` global falha por erros pré-existentes em `scripts/`.
Próxima acção exacta: iniciar o planeamento da Fase 5 com `hcw-plan`, sem tocar nos três screenshots preservados.
Decisões pendentes: validação de HCW-00-006; renomear `STATE.antigo.md` (fora do Git); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini — já tratado como negação segura em HCW-02-005.
