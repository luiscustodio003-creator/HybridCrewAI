# Estado do projecto
Fase actual: 1 · Gate: pendente (6/10 validadas)
Última tarefa validada: HCW-01-006 (2026-11-22) — tarefas validadas em `reports/tasks/HCW-01-006.md`.
A meio: nenhuma tarefa em execução; próxima `HCW-01-007` (persistência SQLite e recuperação após reinício). `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar).
Bloqueios: nenhum; dez commits locais sem push para `origin/master`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-01-007` com `hcw-implement` — `app/core/tasks/store_sqlite.py` com recuperação de tarefas `RUNNING` órfãs para `INTERRUPTED`, teste com `subprocess` real e SQLite real; sem instalar dependências novas.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
