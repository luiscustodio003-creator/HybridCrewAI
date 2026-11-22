# Diário de desenvolvimento
Uma entrada por sessão (formato na Skill `hcw-handoff`). Mais recente em cima.

## 2026-11-22 — HCW-00-001
Feito: `docs/reports/audit.md` declara o projecto de raiz e inventaria Python 3.15.2 global, `.venv` com Python 3.12.0, 100 pacotes em `baseline-freeze.txt`, 25 em `requirements.lock.txt` e a estrutura de pastas actual. Sem segredos em ficheiros do projecto. Tarefa marcada `VALIDATED` com evidência. Criado `.gitignore`, inicializado Git e feito o commit `fd9ac9c` (`HCW-00-001: registar ponto de partida`, 65 ficheiros).
Falhou / por resolver: `pyproject.toml` por criar; `python` da PATH aponta para `C:\Python315`, não para o `.venv`; existe `STATE .md` com espaço no nome, deixado fora do commit; `ruff check scripts tests` aponta 3 erros pré-existentes (2 I001, 1 PLW1510) em `scripts/` e `tests/`, fora do âmbito de HCW-00-001.
Ficheiros tocados: `.gitignore` (novo), `docs/reports/audit.md` (novo), `STATE.md` (novo), `tasks.yaml`, `DEVLOG.md`.
Testes executados: `.venv\Scripts\python.exe -m pytest -q tests/scripts` → `18 passed in 0.60s`; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/check_file_size.py` → 0 erros, 0 avisos; `.venv\Scripts\python.exe -m ruff check scripts tests` → 3 erros pré-existentes; `git status --short` → apenas `?? "STATE .md"` após o commit.
Próxima acção: pedir aprovação ao utilizador para aprovar `HCW-00-003` e continuar a Fase 0; remoto registado para `HCW-00-005`, sem push.

## 2026-11-22 — HCW-00-003
Feito: tarefa aprovada pelo utilizador, executada e validada. Confirmado que, com o ambiente activado do projecto (PATH com `.venv\Scripts`) e no terminal do VS Code, `python` resolve para `.venv/Scripts/python.exe` (3.12.0) através de `python.defaultInterpreterPath` e `python.terminal.activateEnvironment`; `.vscode/settings.json` e `requirements.lock.txt` já estavam na pasta correcta. Criado `docs/reports/hcw-00-003.txt` com a evidência.
Falhou / por resolver: nada nesta tarefa. O `python` global fora do projecto continua `C:\Python315\python.exe` e não foi alterado; `ruff check scripts tests` mantém 3 erros pré-existentes, por resolver em HCW-00-006.
Ficheiros tocados: `tasks.yaml`, `STATE.md`, `DEVLOG.md`, `docs/reports/hcw-00-003.txt` (novo).
Testes executados: `python -m pytest -q tests/scripts` → `18 passed in 0.56s`; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/check_file_size.py` → 0 erros, 0 avisos; `python scripts/lint_skills.py` → 0 erros, 0 avisos; `python scripts/check_modules.py` → 0 erros, 1 aviso (`app/` ainda não existe); `python scripts/plan_status.py` → Fase 00 `2/12`.
Próxima acção: pedir aprovação ao utilizador para aprovar `HCW-00-004` e criar `pyproject.toml`; remoto registado para `HCW-00-005`, sem push.

## 2026-11-22 — HCW-00-004
Feito: tarefa aprovada pelo utilizador, executada e validada. Criado `pyproject.toml` com configuração de `project`, `pytest`, `ruff` (lint, isort e format) e `mypy`. Confirmado que `ruff check`, `mypy --config-file pyproject.toml` e `pytest` leem a configuração sem erros de configuração. Criado `docs/reports/hcw-00-004.txt` com a evidência.
Falhou / por resolver: erros de código pré-existentes continuam visíveis — 5 erros de `ruff` (4 `PLR2004`, 1 `PLW1510`), 3 erros de `mypy` e 13 ficheiros por formatar — todos fora do âmbito desta tarefa e por resolver em `HCW-00-006`. Alterações desta tarefa ainda não cometidas.
Ficheiros tocados: `pyproject.toml` (novo), `docs/reports/hcw-00-004.txt` (novo), `tasks.yaml`, `STATE.md`, `DEVLOG.md`.
Testes executados: `python -m ruff check scripts tests` → 5 erros de código, 0 de configuração; `python -m mypy --config-file pyproject.toml scripts` → 3 erros de tipagem, 0 de configuração; `python -m pytest -q` → 18 testes, sucesso; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/check_file_size.py` → 0 erros, 0 avisos; `python scripts/lint_skills.py` → 0 erros, 0 avisos; `python scripts/check_modules.py` → 0 erros, 1 aviso (`app/` ainda não existe); `python scripts/plan_status.py` → Fase 00 `3/12`.
Próxima acção: pedir aprovação ao utilizador para `HCW-00-005`; ao aprová-la, usar `hcw-plan` para acrescentar a ligação do remoto `origin` antes de implementar; primeiro push só com aprovação explícita.

## 2026-11-22 — HCW-00-005
Feito: tarefa aprovada pelo utilizador e actualizada com `hcw-plan` antes da execução, para incluir a ligação do remoto `origin`. Confirmados os critérios: `.env`, `.venv/` e `logs/` ignorados por `.gitignore`; etiqueta `phase-00-start` criada no commit inicial `fd9ac9c`; remoto `origin` apontando para o repositório indicado pelo utilizador. Criado `docs/reports/hcw-00-005.txt`.
Falhou / por resolver: nada nesta tarefa. Nenhum push foi feito. `HCW-00-006` continua `IMPLEMENTED` com erros de lint/tipagem pré-existentes; `STATE .md` (com espaço) permanece fora do Git.
Ficheiros tocados: `tasks.yaml`, `STATE.md`, `DEVLOG.md`, `docs/reports/hcw-00-005.txt` (novo).
Testes executados: `git check-ignore -v .env .venv/ logs/` → 3 regras do `.gitignore` confirmadas; `git tag -l` → `phase-00-start`; `git show-ref --tags` → `fd9ac9cb5ebfb8202841126ee2cc5f2cde3cb151 refs/tags/phase-00-start`; `git remote -v` → fetch/push para `https://github.com/luiscustodio003-creator/HybridCrewAI`; `python -m pytest -q` → 18 testes, sucesso; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/plan_status.py` → Fase 00 `4/12`.
Próxima acção: pedir aprovação para o commit de `HCW-00-005` e para `HCW-00-007`; primeiro push só com aprovação explícita.

## 2026-11-22 — HCW-00-007
Feito: tarefa aprovada pelo utilizador, executada e validada. Criado `.pre-commit-config.yaml` com sete hooks locais: Ruff (lint e formatação), `check_file_size`, `validate_plan`, `check_modules`, `lint_skills` e `check_traceability`. Sem repos remotos e sem novas instalações. Evidência em `docs/reports/hcw-00-007.txt`.
Falhou / por resolver: nada nesta tarefa. `HCW-00-006` continua `IMPLEMENTED` com erros de lint/tipagem pré-existentes; `STATE .md` (com espaço) permanece fora do Git; nenhum push foi feito.
Ficheiros tocados: `.pre-commit-config.yaml` (novo), `docs/reports/hcw-00-007.txt` (novo), `tasks.yaml`, `STATE.md`, `DEVLOG.md`.
Testes executados: `pre_commit validate-config` → sem erros; ficheiro temporário com 301 linhas em stage → `pre_commit run check-file-size` falhou com `EXIT=1` e mensagem `301 linhas (máximo 300)`; após remoção → `Passed`, `FILE_SIZE_EXIT=0`; `pre_commit run validate-plan --files tasks.yaml` → `Passed`, `PLAN_EXIT=0`; `python -m pytest -q` → 18 testes, sucesso; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/plan_status.py` → Fase 00 `5/12`.
Próxima acção: pedir aprovação para o commit de `HCW-00-007` e para `HCW-00-008`; primeiro push só com aprovação explícita.

## 2026-11-22 — projecto de raiz
Feito: pacote copiado para a raiz; ambiente .venv criado; baseline-freeze guardada.
Decisão: o código anterior foi perdido. HCW-00-002 passa a DEPRECATED; HCW-00-001 passa a registar o arranque de raiz.
Por resolver: mover settings.json para .vscode; Git local; pyproject.toml.
Próxima acção: HCW-00-001.

## 2026-11-22 — arranque
Feito: pacote de Skills, scripts de validação, tasks.yaml (fases 0 a 14), fichas de fase, requisitos iniciais.
Por resolver: auditoria e baseline do código existente; ambiente .venv do utilizador.
Testes executados: tests/scripts (ver relatório da Fase 0).
Próxima acção: HCW-00-001 (auditoria) com a Skill `hcw-audit`.
