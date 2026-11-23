MÓDULO: cli
FINALIDADE: Expor comandos locais para inspeccionar eventos, verificar a instalação e demonstrar o gateway de modelos com segurança.
FUNCIONALIDADES: seguir eventos JSONL em tempo real com filtro por tarefa; verificar configuração, SQLite e redacção com código de saída; testar fornecedores com `llm ping`, redacção antes do envio e consentimento explícito para cloud; ponto de entrada hcw declarado no pyproject.toml.
ESTRUTURA: logs.py (follow, formatar_evento); doctor.py (run, verificações); llm_ping.py (ParametrosPing, SimulatedProvider, run); main.py (parser e despacho); __init__.py (API pública); __main__.py (python -m app.cli); README.txt e module.yaml (documentação).
INTERFACE PÚBLICA: main, follow, formatar_evento, verificar_config, verificar_sqlite, verificar_redaccao, run.
DEPENDÊNCIAS: interna app.core.config, app.core.events, app.core.logging, app.core.tasks, app.llm.contracts, app.llm.consent, app.llm.egress, app.llm.providers; externa apenas biblioteca padrão argparse, json, os, pathlib, sqlite3, sys, time, uuid.
CONFIGURAÇÃO: usa HCW_* existentes e GEMINI_API_KEY por omissão; --base-dir permite apontar o doctor e o consentimento para uma árvore temporária nos testes.
UTILIZAÇÃO: hcw logs --follow --path logs/events.jsonl --task-id <id>; hcw doctor; hcw llm ping --provider simulado; hcw llm ping --provider ollama --endpoint <url>; hcw llm ping --provider gemini --endpoint <url> --allow-cloud.
TESTES: python -m pytest -q tests/integration/test_cli.py tests/integration/test_llm_ping.py
LIMITAÇÕES: o seguimento usa consulta periódica ao ficheiro, não inotify; linhas JSON inválidas são ignoradas; `llm ping` não envia pedidos sem --endpoint e recusa cloud sem --allow-cloud; falhas terminam com código 1 e mensagem redigida.
RELAÇÕES: usa core/events, core/logging, core/config, core/tasks, llm/egress, llm/consent e llm/providers; não é usado por outros módulos nesta fase.
