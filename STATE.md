# Estado do projecto
Fase actual: 1 · Gate: pendente (0/10 validadas)
Última tarefa validada: HCW-00-999 (2026-11-22) — Fase 0 encerrada com GO e etiqueta `phase-00-go` em `d385dce`.
A meio: HCW-01-001 — plano da Fase 1 escrito em `tasks.yaml` com 9 tarefas em `PLANNED` (HCW-01-002 a HCW-01-009); aguarda aprovação. `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar).
Bloqueios: nenhum; três commits locais sem push para `origin/master`.
Próxima acção exacta: pedir ao utilizador que aprove as tarefas HCW-01-002 a HCW-01-009 (passar a `APPROVED` em `tasks.yaml`) e só depois executar `HCW-01-002` com `hcw-implement`; sem instalar dependências novas.
Decisões pendentes: aprovação do plano da Fase 1; validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
