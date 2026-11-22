# Estado do projecto
Fase actual: 0 · Gate: pendente (6/12 validadas)
Última tarefa validada: HCW-00-008 (2026-11-22) — CI real verde em `ubuntu-latest` e `windows-latest` (run `45038923836`); cometida em `aaf34ce`; primeiro push feito para `origin/master`; evidência em `docs/reports/hcw-00-008.txt`
A meio: HCW-00-006 continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar); os hooks de Ruff analisam só ficheiros em stage. A CI não bloqueia por Ruff/mypy enquanto `HCW-00-006` não for corrigido.
Bloqueios: nenhum
Próxima acção exacta: pedir aprovação para a tarefa `HCW-00-009` (`tasks.yaml`: spike do motor de agentes: núcleo próprio vs CrewAI vs LangGraph); não editar `tasks.yaml` para `APPROVED` nem instalar CrewAI/LiteLLM antes dessa aprovação.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; ADR-0001 — motor de agentes, via spike `HCW-00-009`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push futuro só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
