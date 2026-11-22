# Fase 03 — Interface web mínima e Chat de texto

**Objectivo:** Ver o sistema a trabalhar desde cedo. Ecrãs base desenhados no Stitch (opcional) e exportados como andaime.

**Activa (feature flag):** ui

## Entregas principais
- ui/server (app, routes_tasks, routes_events SSE/WebSocket, routes_chat, auth)
- ui/web (index.html, logs.js, tasks.js, llm_calls.js, chat.js, styles.css)
- DESIGN.md

## Testes reais (obrigatórios no gate)
- Playwright: evento aparece no ecrã em menos de 1 s
- Filtro por correlation_id e nível
- Pedido sem token e com Origin inválido recusados; só 127.0.0.1
- Histórico persiste ao reiniciar o servidor
- Funciona offline (CSS compilado localmente)
- Capturas de ecrã como evidência

## Demonstração
Abrir o browser, enviar uma mensagem no chat e ver os eventos em tempo real.

## Gate
Todos os ecrãs com dados reais; testes de segurança local a passar.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
