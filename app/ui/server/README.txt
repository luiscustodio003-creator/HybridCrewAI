MÓDULO: ui/server
FINALIDADE: Servir verificação de saúde, histórico de tarefas e eventos em 127.0.0.1.
FUNCIONALIDADES: criação de ThreadingHTTPServer da biblioteca padrão; recusa de endereços diferentes de 127.0.0.1; GET /health, GET /api/tasks e GET /api/events apenas com ui_enabled ativo; Bearer token; Origin exata http://127.0.0.1:<porta>; respostas curtas em JSON; stream SSE com filtros por correlation_id e level.
ESTRUTURA: app.py (create_server, UiServer e manipulador HTTP); auth.py (origem_valida e pedido_autorizado); routes_tasks.py (serialização e listagem); event_filters.py (filtros); routes_events.py (stream SSE); __init__.py (API pública).
INTERFACE PÚBLICA: EVENTS_PATH, TAREFAS_PATH, EventFilter, analisar_filtros, create_server, filtrar_evento, filtrar_eventos, gerar_eventos_sse, listar_tarefas, origin_local, origem_valida, pedido_autorizado, serializar_tarefa.
DEPENDÊNCIAS: core/config; core/events; core/tasks; biblioteca padrão (collections, dataclasses, hmac, http.server, json, select, socket, threading, time, typing, urllib.parse).
CONFIGURAÇÃO: usa Settings.ui_enabled, Settings.ui_token, Settings.sqlite_path e Settings.event_log; não lê variáveis de ambiente directamente.
UTILIZAÇÃO: servidor = create_server(settings, port=0); tarefa = threading.Thread(target=servidor.serve_forever, daemon=True); pedidos com Authorization: Bearer <token> e Origin: http://127.0.0.1:<porta>; stream em GET /api/events?correlation_id=<id>&level=<nível>.
TESTES: python -m pytest -q tests/unit/test_ui_events.py tests/unit/test_ui_tasks.py tests/integration/test_ui_server.py tests/integration/test_ui_tasks.py tests/integration/test_ui_events_stream.py tests/security/test_ui_local.py
LIMITAÇÕES: ainda não serve HTML; correlation_id das tarefas usa task_id até existir correlação própria persistida; o stream lê o JSONL por sondagem de 0,1 s e mantém keepalive de 1 s, sem bus em memória; logs de pedidos permanecem desligados para não expor token, prompt ou cabeçalhos.
RELAÇÕES: usa app/ui, core/config, core/events e core/tasks; fornece a interface local protegida da Fase 3.
