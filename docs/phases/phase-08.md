# Fase 08 — IMPROVE e controlo de versões (Git)

**Objectivo:** Melhorar projectos existentes de forma pequena, verificável e reversível.

**Activa (feature flag):** improve_git

## Entregas principais
- workflows/improve; change (planner, impact, executor, batch, validator)
- git (detect, status, branches, commits, diff); ecrã Git e alterações

## Testes reais (obrigatórios no gate)
- Repositório Git real: ramo, alteração, testes, commit
- Alterações não guardadas do utilizador nunca são tocadas
- Refactorização de projecto-fixture mantém os testes verdes
- Reverter a tarefa devolve o estado inicial

## Demonstração
Pedir uma melhoria, rever o diff, aprovar e ver o commit.

## Gate
Nenhuma perda de dados do utilizador em todos os cenários.

## Recuperação
Snapshot e etiqueta Git antes de começar; `phase-NN-go` ao fechar.

Antes de implementar: usar a Skill `hcw-plan` para transformar esta ficha em tarefas em `tasks.yaml`.
