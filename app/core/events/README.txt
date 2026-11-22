MÓDULO: core/events
FINALIDADE: Definir o modelo de eventos e distribuí-los por destinos, com persistência JSONL independente por linha.
FUNCIONALIDADES: Evento imutável com correlation_id, task_id, agent e phase; níveis debug/info/warning/error; barramento que entrega a todos os destinos mesmo se um falha; escritor JSONL com bloqueio por instância; leitura de eventos persistidos.
ESTRUTURA: models.py (Event, EventContext, EventLevel e new_event); bus.py (EventBus, EventSink e EventBusError); jsonl_sink.py (JsonlSink e read_events); __init__.py (API pública).
INTERFACE PÚBLICA: Event, EventContext, EventLevel, EventBus, EventBusError, EventSink, JsonlSink, new_event, read_events.
DEPENDÊNCIAS: biblioteca padrão (collections, dataclasses, datetime, enum, json, pathlib, threading, typing, uuid).
CONFIGURAÇÃO: o caminho do ficheiro é injectado por quem cria JsonlSink; normalmente derivado de Settings.log_dir/events_file.
UTILIZAÇÃO: contexto = EventContext(correlation_id=..., task_id=..., agent=..., phase=...); bus = EventBus([JsonlSink(settings.event_log)]); bus.publish(new_event(contexto, kind=..., message=...)).
TESTES: python -m pytest -q tests/unit/test_events.py
LIMITAÇÕES: sem ordenação/distribuição entre processos; o bloqueio é apenas por instância; não redige segredos — usar app.core.config.redact antes de publicar mensagens.
RELAÇÕES: usado por core/logging, core/tasks, core/results, core/security e cli.
