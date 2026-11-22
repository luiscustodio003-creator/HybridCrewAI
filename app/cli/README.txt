MÓDULO: cli
FINALIDADE: Expor comandos locais para inspeccionar eventos e verificar a instalação do HybridCrewAI.
FUNCIONALIDADES: seguir eventos JSONL em tempo real com filtro por tarefa; verificar configuração, SQLite e redacção com código de saída; ponto de entrada hcw declarado no pyproject.toml.
ESTRUTURA: logs.py (follow, formatar_evento); doctor.py (run, verificações); main.py (parser e despacho); __init__.py (API pública); __main__.py (python -m app.cli); README.txt e module.yaml (documentação).
INTERFACE PÚBLICA: main, follow, formatar_evento, verificar_config, verificar_sqlite, verificar_redaccao, run.
DEPENDÊNCIAS: interna app.core.config, app.core.events, app.core.logging, app.core.tasks; externa apenas biblioteca padrão argparse, json, sqlite3, sys, time, pathlib.
CONFIGURAÇÃO: usa HCW_* existentes; --base-dir permite apontar o doctor para uma árvore temporária nos testes.
UTILIZAÇÃO: hcw logs --follow --path logs/events.jsonl --task-id <id>; hcw doctor; python -m app.cli doctor.
TESTES: python -m pytest -q tests/integration/test_cli.py
LIMITAÇÕES: o seguimento usa consulta periódica ao ficheiro, não inotify; linhas JSON inválidas são ignoradas; sem emissão de novos eventos pela CLI.
RELAÇÕES: usa core/events, core/logging, core/config e core/tasks; não é usado por outros módulos nesta fase.
