# Estado do projecto
Fase actual: 1 encerrada · Gate: GO (10/10 validadas)
Última validação: HCW-01-999 (2026-11-22) — gate da Fase 1 em `reports/phase-01/report.md`, resumo em `docs/reports/phase-01.md`.
A meio: nenhuma tarefa em execução; próxima acção é planear a Fase 2 com `hcw-plan` (`HCW-02-001`), mediante aprovação. `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar).
Bloqueios: nenhum para a Fase 1; quinze commits locais sem push para `origin/master`; etiquetas locais `phase-00-go` e `phase-01-go`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: carregar `hcw-router`, confirmar este estado e `python scripts/plan_status.py`, depois usar `hcw-plan` para detalhar `HCW-02-001` (LLM Gateway com política de egress). Não instalar `httpx` nem outras dependências sem aprovação.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
