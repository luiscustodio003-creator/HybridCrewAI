# Fase 04 — MVP vertical: CREATE ponta a ponta

**Objectivo:** Primeiro fluxo completo: pedido, requisitos, plano, arquitectura, aprovação na UI, código com teste, execução, revisão, relatório.

**Activa (feature flag):** create_flow, agentes em Markdown, persona, aprovações na UI

## Entregas principais
- agents/definitions/*.md (um por agente) e agents/runner
- workflows/create
- approvals/tokens (token emitido só pela UI)
- execution/simple_runner (declarado NÃO isolado; só com aprovação)
- persona.md; harness de avaliação com 5 casos

## Testes reais (obrigatórios no gate)
- Caso dourado: calculadora de linha de comandos com testes, pytest aprovado
- Agente que devolve approved=true não aprova nada
- Saída inválida rejeitada e repetida com limite
- Cancelar a meio; matar e retomar
- Cabeçalho de agente inválido recusado com mensagem clara
- 5 casos de referência pontuados

## Demonstração
Pedir uma pequena aplicação no chat, aprovar o plano e ver os agentes trabalhar.

## Gate
5 casos acima da pontuação mínima; recuperação após kill; relatório final gerado.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
