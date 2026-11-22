# Relatório da Fase 01 — Núcleo: configuração, eventos, tarefas, persistência
Data: 2026-11-22 · Gate: GO

## O que foi feito (por tarefa)
- HCW-01-001: plano da Fase 1 revisto com `hcw-plan` e aprovado pelo utilizador; nove tarefas alinhadas com a ficha da fase.
- HCW-01-002: `app/core/config/` com `Settings` imutável, esquema, valores por omissão, validação de caminhos `HCW_*` e `ConfigError`.
- HCW-01-003: `app/core/config/secrets.py` com `SecretStr`, fornecedores injectados, `EnvironmentSecrets` e `redact()`.
- HCW-01-004: `app/core/events/` com modelos de evento, correlacção, barramento e `JsonlSink` com gravação atómica por linha.
- HCW-01-005: `app/core/logging/` com `EventLogger`, destino textual, `SecretRegistry` e redacção de chaves `sk-*`.
- HCW-01-006: `app/core/tasks/` com `Task`, UUIDv5 estável, relógio UTC e máquina de estados; `RUNNING -> INTERRUPTED -> QUEUED` permite retoma.
- HCW-01-007: `SqliteTaskStore` com `initialize`, `save`, `get`, `list_tasks` e `recover_orphans`; teste real de `kill()` e recuperação.
- HCW-01-008: `app/core/results/` com os cinco estados de `ToolResult`; `done` exige evidência não vazia.
- HCW-01-009: `app/cli/` com `hcw logs --follow`, `hcw doctor`, ponto de entrada `hcw` no `pyproject.toml` e launcher local no `.venv`.
- HCW-01-999: gate executado com `GO`; etiqueta `phase-01-go` criada no commit `696ccdb600195fcec5f0a56a91449989a9167528`.

## Comandos executados
Todos com `.venv\Scripts\python.exe`, excepto os comandos Git e o launcher da CLI:
- `python scripts/run_gate.py --phase 1` → `# Gate da Fase 01 — GO`.
- `python -m pytest -q` → 90 testes passam.
- `python -m ruff check app tests/integration/test_cli.py` → `All checks passed!`.
- `python -m mypy app` → `Success: no issues found in 29 source files`.
- `python scripts/check_modules.py` → 0 erros, 0 avisos.
- `python scripts/check_file_size.py` → 0 erros, 0 avisos.
- `python scripts/check_traceability.py` → 0 erros, 0 avisos.
- `python scripts/validate_plan.py` → 0 erros, 0 avisos.
- `python scripts/plan_status.py` → Fase 01 `10/10`; próxima tarefa `HCW-02-001`.
- `cmd /c ".\.venv\Scripts\hcw.cmd doctor"` → `config OK`, `sqlite OK`, `redaction OK`.
- `git tag phase-01-go 696ccdb` → `refs/tags/phase-01-go`.

## Resultados (passam / falham / ignorados)
- Gate: 7 resultados OK — `validate_plan`, `check_file_size`, `check_modules`, `lint_skills`, `check_traceability`, `pytest (13 ficheiros)`, `tarefas da fase concluídas`.
- Testes: 90 passam, 0 falham, 0 ignorados.
- Lint e tipagem de `app/`: sem erros.
- Guardas de plano, módulos, tamanho, Skills e rastreabilidade: sem erros.
- Demonstrações reais: CLI `doctor` sai com `0`; seguimento de eventos mostra `correlation_id` de um evento escrito por subprocesso.

## Critérios de aceitação (um por linha, com a prova)
- `run_gate.py --phase 1 devolve GO` — `reports/phase-01/report.md` e `reports/phase-01/report.json`.
- Recuperação após kill comprovada — `tests/recovery/test_kill_resume.py` e `reports/tasks/HCW-01-007.md`.
- Zero segredos nos logs — `tests/security/test_redaction.py`, `reports/tasks/HCW-01-005.md` e verificação adicional em `reports/tasks/HCW-01-009.md`.
- `ToolResult 'done' sem evidência rejeitado` — `tests/contracts/test_tool_result.py` e `reports/tasks/HCW-01-008.md`.
- `hcw logs --follow` e `hcw doctor` demonstrados com dados reais — `tests/integration/test_cli.py` e `reports/tasks/HCW-01-009.md`.
- Etiqueta `phase-01-go` criada — `git show-ref --tags` aponta para `696ccdb600195fcec5f0a56a91449989a9167528`.
- Configuração sem escrita fora da árvore autorizada — `reports/tasks/HCW-01-002.md`.
- Transições inválidas rejeitadas — `tests/unit/test_state_machine.py` e `reports/tasks/HCW-01-006.md`.
- Eventos JSONL com tipo e dados validados — `reports/tasks/HCW-01-004.md`.

## Segurança (ameaças atacadas nesta fase)
| Ameaça | Contramedida | Teste | Resultado |
|---|---|---|---|
| Perda de trabalho em falhas | Checkpoint SQLite antes do sinal de pronto; `recover_orphans` | `tests/recovery/test_kill_resume.py` com `kill()` real | PASSA |
| Fuga de segredos para logs/cloud | `SecretStr`, `redact()`, `SecretRegistry` e verificação activa do `doctor` | `tests/security/test_redaction.py`; `test_doctor_verifica_config_sqlite_e_redaccao` | PASSA |
| Acção reportada como feita sem o ter sido | `ToolResult` exige evidência para `done`; estados inválidos falham | `tests/contracts/test_tool_result.py` | PASSA |
| Path traversal na configuração | Caminhos `HCW_*` validados e contidos na raiz | `tests/unit/test_config.py` | PASSA |
| Injecção de comandos na CLI | `argparse`, lista fixa de argumentos e subprocesso sem `shell` | `tests/integration/test_cli.py` | PASSA |

## Evidências
- `reports/phase-01/report.md`, `reports/phase-01/report.json`.
- Relatórios por tarefa em `reports/tasks/HCW-01-002.md` a `reports/tasks/HCW-01-009.md`.
- Código em `app/core/` e `app/cli/`, com `README.txt` e `module.yaml` por módulo.
- Testes em `tests/unit/`, `tests/contracts/`, `tests/security/`, `tests/recovery/` e `tests/integration/`.
- Etiqueta local `phase-01-go` no commit `696ccdb600195fcec5f0a56a91449989a9167528`.

## Decisões tomadas (ADR e IDs)
- ADR-0001 mantém-se aceite: núcleo próprio e fino, sem CrewAI/LiteLLM instalados; adaptadores futuros ficam atrás de portas estáveis.
- Nenhuma dependência nova foi instalada na Fase 1.
- Os testes de recuperação e redacção usam ficheiros, SQLite e subprocessos reais; mocks apenas onde já previstos para falhas de fornecedores.

## Problemas pendentes e limitações conhecidas
- `HCW-00-006` continua `IMPLEMENTED`: 5 erros de `ruff`, 3 de `mypy` e 13 ficheiros por formatar em `scripts/`. O gate usa os scripts directamente e não os aponta como bloqueantes.
- O launcher `.venv\Scripts\hcw.cmd` é local ao ambiente virtual; o ponto de entrada versionado é `hcw = "app.cli:main"` em `pyproject.toml`.
- Ainda não há servidor, interface web, chamada ao Gemini, workspace nem execução isolada; essas superfícies começam nas Fases 2 a 6.
- O ficheiro legado `STATE .md` (com espaço) continua fora do Git; remoção exige decisão do utilizador.
- Push para `origin/master` não foi autorizado; todos os commits e a etiqueta são locais.
- Decisões em aberto: P-02, P-03, P-04 e P-05.

## Ideias adiadas (IDEA-xxx)
- IDEA-003 REA como extensão MCP — Fase 13, depende de P-03.
- IDEA-005 ferramentas de redes — Fase 12, depende de P-02.
- IDEA-006 persona do assistente — Fase 4.
- IDEA-007 resumos proactivos — Fase 9.
- IDEA-008 controlo do computador — Fase 12, sempre com confirmação.

## Como demonstrar (passos para o utilizador ver a funcionar)
1. Abrir `reports/phase-01/report.md` e confirmar o veredicto GO e os sete resultados OK.
2. Correr `.venv\Scripts\python.exe -m pytest -q` e ver os 90 testes a passar.
3. Correr `cmd /c ".\.venv\Scripts\hcw.cmd doctor"` e ver `config OK`, `sqlite OK`, `redaction OK`.
4. Correr `.venv\Scripts\python.exe scripts/plan_status.py`: Fase 01 encerrada e próxima tarefa `HCW-02-001`.
5. Correr `git show-ref --tags` e confirmar `phase-01-go`.
