# Estado do projecto
Fase actual: 0 · Gate: pendente (7/12 validadas)
Última tarefa validada: HCW-00-009 (2026-11-22) — spike documental do motor de agentes; relatório em `docs/reports/spike-agent-engine.md`; sem CrewAI, LiteLLM ou LangGraph instalados
A meio: `HCW-00-006` continua `IMPLEMENTED` (scripts com 18 testes a passar, mas 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar); os hooks de Ruff analisam só ficheiros em stage. A CI não bloqueia por Ruff/mypy enquanto `HCW-00-006` não for corrigido.
Bloqueios: nenhum
Próxima acção exacta: pedir aprovação ao utilizador para abrir `HCW-00-010` e escrever `docs/adr/ADR-0001-motor-de-agentes.md` com a decisão do motor, usando `docs/reports/spike-agent-engine.md` como evidência; não instalar dependências sem ADR aprovado.
Decisões pendentes: validação de `HCW-00-006`; renomear `STATE .md` (com espaço, fora do Git) para `STATE.md`; ADR-0001 — motor de agentes, agora com base no spike `HCW-00-009`; P-02 ferramentas de redes; P-03 finalidade do REA; P-04 hardware; P-05 tipo de conta Gemini. Push futuro só com aprovação explícita (sem `--force`, sem mudar histórico, sem apagar ramos).
