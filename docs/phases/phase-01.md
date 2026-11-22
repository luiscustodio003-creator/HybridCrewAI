# Fase 01 — Núcleo: configuração, eventos, tarefas, persistência

**Objectivo:** A espinha dorsal que tudo o resto usa.

**Activa (feature flag):** core

## Entregas principais
- app/core/config (schema, loader, defaults, secrets)
- app/core/events (models, bus, jsonl_sink)
- app/core/tasks (model, state_machine, store_sqlite, ids)
- app/core/logging (setup, correlation, redaction)
- app/core/results (ToolResult)
- app/cli (logs, doctor)

## Testes reais (obrigatórios no gate)
- Tarefa real com SQLite real: criar, correr, concluir
- Matar o processo a meio e recuperar o estado
- Transições inválidas rejeitadas
- Chave falsa nunca aparece nos logs
- ToolResult 'done' sem evidência é rejeitado
- hcw logs --follow mostra eventos reais

## Demonstração
Correr uma tarefa, matar o processo, relançar e ver a tarefa retomar.

## Gate
Recuperação após kill comprovada; zero segredos nos logs; hcw doctor verde.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
