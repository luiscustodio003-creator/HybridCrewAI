# Estado do projecto
Fase actual: 1 · Gate: pendente (9/10 validadas)
Última tarefa validada: HCW-01-009 (2026-11-22) — CLI validada em `reports/tasks/HCW-01-009.md`.
A meio: nenhuma tarefa em execução; próximo passo é o gate da Fase 1 (`HCW-01-999`). `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar).
Bloqueios: nenhum; catorze commits locais sem push para `origin/master`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `python scripts/run_gate.py --phase 1` com `hcw-test-gate`; com `GO`, validar o gate, escrever `docs/reports/phase-01.md`, criar a etiqueta `phase-01-go`, actualizar este ficheiro e terminar com `hcw-handoff`.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
