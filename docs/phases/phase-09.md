# Fase 09 — Autonomia, tarefas em segundo plano e rotinas

**Objectivo:** Agentes a trabalhar sozinhos com limites, e um assistente proactivo.

**Activa (feature flag):** background_tasks, rotinas, horas de silêncio, orçamentos, centro de comando

## Entregas principais
- autonomy (budgets, checkpoints, resume, kill_switch)
- routines (engine, schedule, quiet_hours, late_policy)
- ecrãs Custos/quotas/rotinas e Centro de comando

## Testes reais (obrigatórios no gate)
- Tarefa longa interrompida por kill retoma sem repetir passos
- Orçamento esgotado: pausa com resultado parcial guardado
- Botão de paragem deixa tudo consistente
- Interrompida três vezes passa a FAILED
- Rotina que vence durante o silêncio segue a política de atraso
- Duas tarefas em projectos diferentes não misturam dados

## Demonstração
Pedir 'faz isto durante dez minutos', continuar a conversar e receber o aviso no fim.

## Gate
Nível L2 validado; L3 só se todos os testes de orçamento e paragem passarem.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
