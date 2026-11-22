# Fase 10 — Memória e conhecimento

**Objectivo:** O assistente lembra-se de decisões e contexto, projecto a projecto.

**Activa (feature flag):** memory

## Entregas principais
- knowledge (store, project_memory, engineering_memory, session_memory, search, retention)
- SQLite + FTS5; índice de chaves + ferramenta recall_memory; ecrã Memória

## Testes reais (obrigatórios no gate)
- Decisão guardada é citada após reiniciar
- Memória do projecto A nunca aparece no B
- Facto fora do núcleo encontrado via índice de chaves
- Eliminar funciona e deixa de ser recuperável
- Segredos não são guardados

## Demonstração
Perguntar 'o que decidimos sobre X?' numa sessão nova.

## Gate
Isolamento entre projectos a 100%; recuperação relevante nos casos de referência.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
