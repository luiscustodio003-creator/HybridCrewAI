# Estado do projecto
Fase actual: 0 · Gate: pendente (5/12 validadas)
Última tarefa validada: HCW-00-007 (2026-11-22) — `.pre-commit-config.yaml` com Ruff e guardas locais; evidência em `docs/reports/hcw-00-007.txt`
A meio: HCW-00-006 continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar); os hooks de Ruff analisam só ficheiros em stage
Bloqueios: nenhum
Próxima acção exacta: pedir aprovação para o commit de `HCW-00-007` e para a tarefa `HCW-00-008` (configurar CI em GitHub Actions para Windows e Linux)
Decisões pendentes: commit de `HCW-00-007`; primeiro push só com aprovação explícita do utilizador (sem `--force`, sem mudar histórico, sem apagar ramos); validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; ADR-0001 — motor de agentes, via spike `HCW-00-009` (não instalar CrewAI nem LiteLLM antes da decisão); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini
