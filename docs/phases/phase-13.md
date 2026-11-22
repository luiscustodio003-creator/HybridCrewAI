# Fase 13 — Engenharia reversa (extensão REA via MCP)

**Objectivo:** Analisar binários, apps sem código-fonte, Electron e APK, como extensão opcional do modo ANALYZE.

**Activa (feature flag):** reverse_eng

## Entregas principais
- tools/reverse (adaptador MCP do REA, versão fixada, origem oficial)
- aviso legal e registo da finalidade; análise só no sandbox

## Testes reais (obrigatórios no gate)
- Binário inofensivo e app JavaScript pequena analisados com evidência
- Ficheiro fora do workspace bloqueado
- Instalação sem aprovação recusada
- Prompt injection nas strings não altera o agente
- Sem rede, no sandbox, sem processos órfãos

## Demonstração
Analisar um binário de teste e abrir o relatório.

## Gate
Testes de isolamento a 100%; contrato Tool isola o sistema de mudanças do REA. Pendente: P-03 (finalidade).

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
