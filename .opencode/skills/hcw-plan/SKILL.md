---
name: hcw-plan
description: Cria e actualiza tarefas HCW-FF-NNN em tasks.yaml a partir da ficha de uma fase. Usar quando uma fase vai começar, quando o utilizador pedir "planear a fase N", "detalhar tarefas", "acrescentar uma tarefa", alterar prioridades ou dependências, ou quando uma ideia aprovada tem de virar trabalho concreto.
---

# Planeamento por fase (just-in-time)

As fases 2 a 14 só têm as tarefas `-001` (planear) e `-999` (gate). Detalham-se quando chegam, com o que se aprendeu nas fases anteriores.

## Procedimento
1. Ler `docs/phases/phase-NN.md`, `docs/requirements.yaml` e o `STATE.md`.
2. Inspeccionar o código afectado (`hcw-audit` se ainda não houver auditoria recente) para não duplicar nada.
3. Criar entre 6 e 12 tarefas pequenas (cada uma implementável numa sessão), com o modelo `templates/TASK_TEMPLATE.yaml`: ID, título, requisitos, dependências, ficheiros novos e a alterar, testes (caminhos reais) e critérios de aceitação verificáveis.
4. Acrescentar as novas tarefas ao `depends_on` do gate `HCW-NN-999`.
5. Estado inicial `PLANNED`. Correr `python scripts/validate_plan.py`.
6. Mostrar o plano ao utilizador. **Só ele passa as tarefas a `APPROVED`.**

## Regras
- Alterações localizadas: nunca reescrever o `tasks.yaml` inteiro; nunca apagar tarefas (usar `DEPRECATED` e ligar à substituta).
- Cada requisito novo entra em `docs/requirements.yaml` (tipos FR, NFR, SEC, OPS, UI, DOC).
- Critérios de aceitação mensuráveis («rejeita ZIP com `../`»), nunca vagos («funciona bem»).
- Tarefas que tocam em segurança incluem o teste de ataque correspondente (`hcw-security-review`).
