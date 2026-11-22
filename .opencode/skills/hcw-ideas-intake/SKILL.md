---
name: hcw-ideas-intake
description: Regista qualquer ideia, pedido novo ou mudança de âmbito do HybridCrewAI na caixa de ideias antes de se perder. Usar sempre que o utilizador disser "e se...", "também podíamos", "não sei se faz sentido", sugerir uma ferramenta, biblioteca ou funcionalidade nova, ou quando o agente tiver vontade de acrescentar algo fora do plano.
---

# Caixa de ideias

Ideias novas **nunca** entram directamente no código nem em `tasks.yaml`. Passam por `IDEAS.md`.

## Procedimento
1. Acrescentar uma linha à tabela de `IDEAS.md` com o modelo `templates/IDEA_TEMPLATE.md`: ID `IDEA-NNN`, descrição, estado `PROPOSTA`, fase provável e motivo.
2. Avaliar em 3 linhas: valor, custo/risco, fase onde encaixa e se contradiz alguma decisão (`D-xx`).
3. Mostrar ao utilizador e pedir decisão: `APROVADA`, `ADIADA` ou `REJEITADA`.
4. Só se `APROVADA`: usar `hcw-plan` para criar a tarefa e ligar a um requisito.
5. Se afectar a arquitectura, abrir ADR (`hcw-docs`).

## Estados
`PROPOSTA` · `APROVADA` · `ADIADA` · `REJEITADA`. Nunca apagar ideias; mudar o estado e escrever o motivo.

## Porquê
Evita o desvio de âmbito (o maior risco do projecto) sem perder boas ideias.
