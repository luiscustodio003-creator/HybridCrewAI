# Estado do projecto
Fase actual: 0 · Gate: pendente (5/12 validadas)
Última tarefa validada: HCW-00-007 (2026-11-22) — cometida em `be5a1bd`; `.pre-commit-config.yaml` com Ruff e guardas locais; evidência em `docs/reports/hcw-00-007.txt`
A meio: HCW-00-008 está `IMPLEMENTED`: `.github/workflows/ci.yml` corrige Windows/Linux com Python 3.12, guardas, pytest e validação do pre-commit; evidência em `docs/reports/hcw-00-008.txt`. Falta commit, primeiro push e ver o CI verde nos runners reais. HCW-00-006 continua `IMPLEMENTED` com erros pré-existentes de Ruff/mypy.
Bloqueios: nenhum comando falhou; commit de HCW-00-008 e primeiro push ainda não autorizados.
Próxima acção exacta: pedir ao utilizador autorização para o commit `HCW-00-008` e para o primeiro push, de forma a observar a CI real em `ubuntu-latest` e `windows-latest`.
Decisões pendentes: commit de `HCW-00-008`; primeiro push só com aprovação explícita do utilizador (sem `--force`, sem mudar histórico, sem apagar ramos); validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; ADR-0001 — motor de agentes, via spike `HCW-00-009` (não instalar CrewAI nem LiteLLM antes da decisão); P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini
