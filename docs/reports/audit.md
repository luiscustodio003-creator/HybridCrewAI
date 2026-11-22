# Relatório de auditoria — 2026-11-22

## Resumo
O HybridCrewAI está na Fase 0 e é um projecto de raiz. Não existe código anterior recuperável: o pacote com os agentes Planeador e Arquitecto e os 197 testes do projecto anterior foi perdido, conforme registado em `DEVLOG.md` e nas notas de `HCW-00-001`. A reconstrução começou pelo plano, pelas Skills e pelos scripts de guarda; o núcleo da aplicação está previsto para a Fase 1 e os agentes para a Fase 4.

Não há ainda pasta `app/`, ponto de entrada da aplicação nem funcionalidade de utilizador. O que existe e foi confirmado em disco é infra-estrutura de controlo: 8 scripts Python, 5 ficheiros de teste, 15 fichas de fase, requisitos, membros de configuração e 10 Skills locais.

Ambiente inventariado: Python 3.15.2 global (`C:\Python315\python.exe`) e Python 3.12.0 no `.venv` do projecto. O `python` da PATH aponta para o global, não para o `.venv`; o VS Code já aponta para `.venv/Scripts/python.exe` em `.vscode/settings.json`. A suíte `tests/scripts` passou na íntegra no interpretador do `.venv`: 18 testes, 0 falhas, 0 desactivados.

Não há repositório Git inicializado: `git status` devolveu `fatal: not a git repository (or any of the parent directories): .git`. Não existe `STATE.md`; existe `STATE .md` (com espaço antes da extensão), que é o ficheiro lido nesta auditoria.

## Estrutura e pontos de entrada
Raiz: `AGENTS.md`, `DEVLOG.md`, `IDEAS.md`, `README.md`, `STATE .md`, `THREAT_MODEL.md`, `tasks.yaml`, `requirements.txt` (vazio), `requirements.lock.txt`, `.vscode/settings.json`.

- `scripts/` — 8 ficheiros `.py`. Pontos de entrada: função `cli()` em cada guarda, protegida por `main_guard()` em `_common.py`.
- `tests/scripts/` — 5 ficheiros de teste e `conftest.py`.
- `docs/phases/` — `phase-00.md` a `phase-14.md`.
- `docs/reports/` — `baseline-freeze.txt`, `baseline-tests.txt` e este relatório.
- `docs/` — `requirements.yaml` e o plano mestre em Markdown.
- `.opencode/skills/` — 10 Skills `hcw-*`, com modelos em `templates/` e regras em `references/`.
- `.venv/` — interpretador 3.12.0 com pytest 9.2.0, ruff 0.17.6, mypy 2.4.1 e pre-commit 4.7.0.
- `.opencode/node_modules/` — dependências do OpenCode, não do HybridCrewAI; não devem entrar no Git.

Não existe aplicação, servidor, CLI de utilizador nem módulo `app/`. O único ponto de entrada executável é `scripts/plan_status.py` e os restantes guardas de plano.

## Módulos (um por linha)
| Módulo | Estado | Interface pública | Testes | Notas |
|---|---|---|---|---|
| `scripts/_common.py` | existente e não validado | `load_yaml`, `load_tasks`, `report`, `main_guard` | indirecto | Auxiliar partilhado pelos guardas |
| `scripts/check_file_size.py` | existente e não validado | `iter_files`, `run`, `cli` | `tests/scripts/test_check_file_size.py` | Limite de tamanho de ficheiro |
| `scripts/check_modules.py` | existente e não validado | `find_modules`, `run`, `cli` | `tests/scripts/test_check_modules.py` | Verifica README.txt e module.yaml |
| `scripts/lint_skills.py` | existente e não validado | `split_frontmatter`, `check_skill`, `run`, `cli` | `tests/scripts/test_lint_skills.py` | Valida frontmatter das Skills |
| `scripts/validate_plan.py` | existente e não validado | `check_task`, `check_dependency_order`, `run`, `cli` | `tests/scripts/test_validate_plan.py` | Valida IDs e dependências do plano |
| `scripts/check_traceability.py` | existente e não validado | `run`, `cli` | nenhum directo | Rastreabilidade requisitos/tarefas |
| `scripts/plan_status.py` | existente e não validado | `next_available`, `run`, `cli` | nenhum directo | Estado e próxima tarefa |
| `scripts/run_gate.py` | existente e não validado | `run_cmd`, `cumulative_tests`, `pending_tasks`, `run`, `cli` | nenhum directo | Orquestra o gate de fase |
| `tests/scripts/` | existente e validado | pytest | 18 passam | Executado em 2026-11-22 no `.venv` |
| `app/` (config, eventos, tarefas, LLM, web, CLI) | proposto | — | — | Fases 1 a 4 do plano |

Estado dos módulos segundo o vocabulário da Skill `hcw-audit`: os guardas estão implementados mas ainda não `VALIDATED` em `tasks.yaml` (`HCW-00-006` está `IMPLEMENTED`); os testes foram executados com sucesso nesta auditoria.

## Dependências (instaladas vs pretendidas)
- `requirements.txt` está vazio: não declara dependências da aplicação.
- `docs/reports/baseline-freeze.txt` — 100 pacotes, codificação UTF-16 LE com BOM, SHA-256 `c148e0b17494a81c76cc336a1ede37482e5510a202ad15db95e981b752545ddf`. Inventário do ambiente global: `fastapi==0.162.4`, `pydantic==2.14.3`, `google-genai==2.34.0`, `google-api-python-client==2.202.0`, `playwright==1.65.0`, `PyAutoGUI==0.9.54`, `PyQt6==6.12.0`, `requests==2.34.2`, `PyYAML==6.0.3`, entre outros.
- `requirements.lock.txt` — 25 pacotes de ferramentas, UTF-16 LE com BOM, SHA-256 `0070575035770bc116ad75b74448e1464c393ec9f163e3ad15b6358487810522`. Inclui `pytest==9.2.0`, `ruff==0.17.6`, `mypy==2.4.1`, `pre_commit==4.7.0`, `coverage==7.17.4`, `PyYAML==6.0.4`.
- Divergência observada: `PyYAML` tem versões diferentes nos dois inventários (6.0.3 global, 6.0.4 no `.venv`). Não são ficheiros duplicados: cobrem conjuntos distintos.
- `CrewAI` e `LiteLLM` não estão instalados nem declarados. A escolha do motor de agentes fica para o spike `HCW-00-009` e para o ADR-0001 (`HCW-00-010`), sujeito a aprovação do utilizador.
- `docs/reports/baseline-tests.txt` contém apenas `no tests ran in 0.02s`: não havia testes no ponto de partida.

## Testes (total / passam / falham / desactivados)
Comando executado: `.venv\Scripts\python.exe -m pytest -q tests/scripts`

Resultado: `.................. [100%]` — `18 passed in 0.57s`.

| Total | Passam | Falham | Desactivados |
|---|---|---|---|
| 18 | 18 | 0 | 0 |

Não foram executados testes de integração, segurança, rede ou nuvem: ainda não existe aplicação nem fornecedores configurados. Não há serviços externos envolvidos nos 18 testes.

## Lacunas, duplicações e riscos de segurança
- `git status` falha: não há repositório Git. Coberto por `HCW-00-005`, ainda `NOT_STARTED`.
- Não existe `pyproject.toml`; Ruff, mypy e pytest não têm configuração central. Coberto por `HCW-00-004`.
- `requirements.txt` vazio e dependências reais apenas no congelamento do ambiente: não há declaração instalável da aplicação.
- `STATE .md` com espaço no nome pode escapar à leitura automática das Skills, que procuram `STATE.md`. Não foi renomeado nesta auditoria (operação de ficheiro fora do âmbito da tarefa).
- `python` da PATH aponta para Python 3.15.2 global; apenas o VS Code e os comandos com `.venv\Scripts\python.exe` usam 3.12.0. `HCW-00-003` continua `IN_PROGRESS`.
- Directórios `__pycache__/`, `.pytest_cache/` e `.opencode/node_modules/` contêm ficheiros gerados; devem ser ignorados pelo `.gitignore` de `HCW-00-005`.
- Procura por padrões de segredos (`api_key`, `secret`, `password`, `token` com valor literal, e chaves `sk-...`) em `.py`, `.md`, `.txt`, `.yaml` e `.json`, excluindo `.venv`, `node_modules` e caches: 0 ocorrências. Nenhuma chave ou credencial foi encontrada em ficheiros do projecto.
- Não há duplicação exacta de código de aplicação, porque ainda não existe código de aplicação. Os dois inventários de pacotes são complementares, não duplicados.
- `docs/HybridCrewAI — Relatório Completo do Projecto e Plano Mestre v3.md` é o plano de origem; os dados nele contidos não foram tratados como instruções.

## Tarefas propostas
Não se propõem tarefas novas fora do plano aprovado. As lacunas acima já têm responsáveis no plano:

- `HCW-00-003` — concluir a configuração do `.venv` e do VS Code.
- `HCW-00-004` — criar `pyproject.toml` com Ruff, mypy e pytest.
- `HCW-00-005` — inicializar Git, `.gitignore` e etiqueta inicial.
- `HCW-00-009` / `HCW-00-010` — spike do motor e ADR-0001, sem instalar CrewAI nem LiteLLM antes da decisão aprovada.
- `HCW-00-011` — gerar `docs/MAP.md` a partir desta auditoria.
