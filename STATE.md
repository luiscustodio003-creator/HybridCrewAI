# Estado do projecto
Fase actual: 1 · Gate: pendente (4/10 validadas)
Última tarefa validada: HCW-01-004 (2026-11-22) — eventos validados em `reports/tasks/HCW-01-004.md`.
A meio: nenhuma tarefa em execução; próxima `HCW-01-005` (logging). `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar).
Bloqueios: nenhum; oito commits locais sem push para `origin/master`; `ruff check .` global ainda falha por 5 erros pré-existentes em `scripts/`.
Próxima acção exacta: executar `HCW-01-005` com `hcw-implement` — logging central com correlação e redacção de segredos em `app/core/logging/`, ligando `redact()` e `EventBus`; sem instalar dependências novas.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push das fases 0 e 1 só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
