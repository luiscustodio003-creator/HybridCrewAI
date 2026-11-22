# Relatório da Fase 00 — Fundação, auditoria e escolha do motor
Data: 2026-11-22 · Gate: GO

## O que foi feito (por tarefa)
- HCW-00-001: auditoria do projecto de raiz, sem código anterior recuperável; registada a baseline do ambiente.
- HCW-00-002: `DEPRECATED` — os 197 testes históricos não existem em disco.
- HCW-00-003: `.venv` com Python 3.12.0 e VS Code apontado para o interpretador do projecto.
- HCW-00-004: `pyproject.toml` com configuração de Ruff, mypy e pytest.
- HCW-00-005: Git inicializado, `.gitignore`, etiqueta `phase-00-start` e remoto `origin` configurados.
- HCW-00-006: oito scripts de guarda em `scripts/` com 18 testes em `tests/scripts/`; permanece `IMPLEMENTED` por erros de lint/tipagem pré-existentes.
- HCW-00-007: `.pre-commit-config.yaml` com sete hooks locais (Ruff, tamanho de ficheiro, plano, módulos, Skills, rastreabilidade).
- HCW-00-008: `.github/workflows/ci.yml` com matriz Windows/Linux; ambos os runners verdes nos runs 45038923836 e 45039146828.
- HCW-00-009: spike documental do motor de agentes com o mesmo cenário em núcleo próprio, CrewAI e LangGraph.
- HCW-00-010: ADR-0001 escolhe núcleo próprio com adaptadores futuros para CrewAI e LangGraph; aceite pelo utilizador.
- HCW-00-011: `docs/MAP.md` com responsabilidades, pastas e ficheiros principais, fechando a auditoria.
- HCW-00-999: gate executado com GO; etiqueta `phase-00-go` criada no commit `d385dce`.

## Testes e evidências
Comandos executados (todos no interpretador do `.venv`, excepto os comandos Git):
- `.venv\Scripts\python.exe scripts/run_gate.py --phase 0` → saída `GO`, `GATE_EXIT=0`.
- O gate correu `validate_plan`, `check_file_size`, `check_modules`, `lint_skills`, `check_traceability`, `pytest` (4 ficheiros) e a verificação de tarefas pendentes: sete resultados OK.
- `.venv\Scripts\python.exe -m pytest -q` → 18 testes passam no total acumulado até esta fase.
- `git tag phase-00-go` → `refs/tags/phase-00-go` aponta para `d385dce987f0b589763bf32a0b9c8635ec4b8be3`.

Critérios de aceitação do gate:
- `run_gate.py --phase 0 devolve GO` — prova em `reports/phase-00/report.md` e `reports/phase-00/report.json`.
- `etiqueta phase-00-go criada` — prova em `git show-ref --tags`.

Evidências: `reports/phase-00/report.md`, `reports/phase-00/report.json`, `docs/reports/baseline-tests.txt`, `docs/reports/hcw-00-005.txt`, `docs/reports/hcw-00-007.txt`, `docs/reports/hcw-00-008.txt`, `docs/reports/spike-agent-engine.md`, `docs/adr/ADR-0001-motor-de-agentes.md`, `docs/MAP.md`.

## Decisões tomadas (ADR e IDs)
- ADR-0001 (ACEITE): motor próprio, sem CrewAI nem LiteLLM instalados; adaptadores futuros previstos mas não implementados.
- Estrutura de controlo: Skills locais, guardas Python, CI em duas plataformas e plano em `tasks.yaml` como fonte de estado.

## Limitações conhecidas
- Não há aplicação, ponto de entrada de utilizador nem pasta `app/`; `check_modules` devolveu um aviso por isso. A funcionalidade começa na Fase 1.
- A baseline histórica de 197 testes foi perdida; a evidência actual são os 18 testes em `tests/scripts/`.
- `HCW-00-006` continua `IMPLEMENTED`: 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar. O gate não os trata como bloqueantes; a correção deve ser planeada na Fase 1.
- O ficheiro legado `STATE .md` (com espaço) continua fora do Git, à espera de decisão do utilizador.
- A etiqueta `phase-00-go` e o commit de encerramento não foram enviados para `origin`; push exige aprovação explícita.
- Não foram executados testes de rede, cloud ou segurança activa: ainda não há superfície de aplicação. O `THREAT_MODEL.md` da Fase 0 limita-se às ameaças de infra-estrutura já tratadas pelo CI e pelo `.gitignore`.

## Ideias adiadas (IDEA-xxx)
- IDEA-003 REA como extensão MCP — Fase 13, depende de P-03.
- IDEA-005 ferramentas de redes — Fase 12, depende de P-02.
- IDEA-006 persona do assistente — Fase 4.
- IDEA-007 resumos proactivos — Fase 9.
- IDEA-008 controlo do computador — Fase 12, sempre com confirmação.
- Decisões em aberto registadas em `STATE.md`: P-02, P-03, P-04 e P-05.

## Como demonstrar (passos para o utilizador ver a funcionar)
1. Abrir `reports/phase-00/report.md` e confirmar o veredicto GO e os sete resultados OK.
2. Abrir `docs/MAP.md` e `docs/adr/ADR-0001-motor-de-agentes.md`.
3. Correr `.venv\Scripts\python.exe scripts/run_gate.py --phase 0` e `git show-ref --tags`.
4. Consultar `python scripts/plan_status.py`: Fase 00 encerrada e próxima tarefa `HCW-01-001`.
