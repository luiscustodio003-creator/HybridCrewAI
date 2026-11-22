# Diário de desenvolvimento
Uma entrada por sessão (formato na Skill `hcw-handoff`). Mais recente em cima.

## 2026-11-22 — HCW-00-001
Feito: `docs/reports/audit.md` declara o projecto de raiz e inventaria Python 3.15.2 global, `.venv` com Python 3.12.0, 100 pacotes em `baseline-freeze.txt`, 25 em `requirements.lock.txt` e a estrutura de pastas actual. Sem segredos em ficheiros do projecto. Tarefa marcada `VALIDATED` com evidência.
Falhou / por resolver: `git status` falha (sem repositório); `pyproject.toml` por criar; `python` da PATH aponta para `C:\Python315`, não para o `.venv`; existe `STATE .md` com espaço no nome; `ruff check scripts tests` aponta 3 erros pré-existentes (2 I001, 1 PLW1510) em `scripts/` e `tests/`, fora do âmbito de HCW-00-001.
Ficheiros tocados: `docs/reports/audit.md` (novo), `STATE.md` (novo), `tasks.yaml`, `DEVLOG.md`.
Testes executados: `.venv\Scripts\python.exe -m pytest -q tests/scripts` → `18 passed in 0.60s`; `python scripts/validate_plan.py` → 0 erros, 0 avisos; `python scripts/check_traceability.py` → 0 erros, 0 avisos; `python scripts/check_file_size.py` → 0 erros, 0 avisos; `.venv\Scripts\python.exe -m ruff check scripts tests` → 3 erros pré-existentes.
Próxima acção: pedir aprovação para o `git commit` de HCW-00-001; a continuação da Fase 0 depende de novas aprovações.

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
