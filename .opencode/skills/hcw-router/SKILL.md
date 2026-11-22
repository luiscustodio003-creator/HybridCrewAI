---
name: hcw-router
description: Porta de entrada de TODO o trabalho no projecto HybridCrewAI. Usar sempre que o utilizador disser continuar, avançar, implementar, construir, planear, auditar, testar, documentar, "em que ponto estamos", ou mencionar uma fase, tarefa HCW-XX-NNN, gate ou o plano. Escolhe a Skill certa e aplica as regras globais do projecto.
---

# HybridCrewAI — router

Objectivo: nunca trabalhar às cegas. Antes de qualquer acção, ficar a saber onde o projecto está.

## Primeiro passo (sempre)
1. Ler `STATE.md` e as últimas entradas de `DEVLOG.md`.
2. Correr `python scripts/plan_status.py` para ver a fase, o progresso e a próxima tarefa.
3. Escolher a Skill pela tabela e carregá-la.

| Pedido do utilizador | Skill |
|---|---|
| «continua», «faz a fase N», «avança» | `hcw-phase-runner` |
| Detalhar ou alterar tarefas | `hcw-plan` |
| Implementar uma tarefa aprovada | `hcw-implement` |
| Correr testes, fechar tarefa ou fase | `hcw-test-gate` |
| Ver o estado actual do código | `hcw-audit` |
| Mexer em ficheiros, execução, rede, credenciais, cloud | `hcw-security-review` |
| Escrever README, ADR, relatórios | `hcw-docs` |
| Surgiu uma ideia nova | `hcw-ideas-intake` |
| Início ou fim de sessão | `hcw-handoff` |

## Regras globais (valem sempre)
- Inspeccionar antes de alterar; reutilizar antes de criar; não inventar APIs nem bibliotecas.
- Um ficheiro, uma responsabilidade; máximo 300 linhas (aviso aos 200).
- Uma tarefa de cada vez; só `VALIDATED` com evidência real.
- O modelo propõe, o Python executa; nunca executar texto do modelo como comando.
- Nunca guardar segredos em ficheiros, logs ou no Git.
- Documentação e comentários em PT-PT; identificadores e nomes de ficheiros em inglês.
- Aprovar planos, decisões e alterações destrutivas é do utilizador, nunca do agente.
- Se faltar informação, perguntar em vez de adivinhar. Terminar sempre com `hcw-handoff`.
