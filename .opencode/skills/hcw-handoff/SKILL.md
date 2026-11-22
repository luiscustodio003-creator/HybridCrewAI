---
name: hcw-handoff
description: Garante a continuidade entre sessões do HybridCrewAI. Usar no INÍCIO de qualquer sessão (para ler o estado) e no FIM (para gravar o ponto exacto onde ficou, a próxima acção e os bloqueios), sempre que o utilizador disser "paro por hoje", "retomar", "onde ficámos" ou antes de a conversa ficar demasiado longa.
---

# Continuidade entre sessões

## Ao começar
1. Ler `STATE.md` (uma página) e as 3 últimas entradas de `DEVLOG.md`.
2. Correr `python scripts/plan_status.py` e `git status`.
3. Confirmar com o utilizador a «próxima acção exacta» registada. Se o `git status` mostrar alterações que o `STATE.md` não explica, perguntar antes de tocar.

## Ao terminar (ou antes de a conversa ficar longa)
1. Actualizar `tasks.yaml`: estados reais; `VALIDATED` só com evidência.
2. Reescrever `STATE.md` pelo modelo em `templates/STATE_TEMPLATE.md`: fase, última tarefa validada, o que está a meio, bloqueios, **próxima acção exacta** (um comando ou um ficheiro concreto) e decisões pendentes.
3. Acrescentar uma entrada ao `DEVLOG.md` (formato abaixo).
4. Registar ideias novas em `IDEAS.md` (`hcw-ideas-intake`).
5. `python scripts/validate_plan.py` e `git commit` com o ID da tarefa.

## Formato da entrada do DEVLOG
```
## AAAA-MM-DD — sessão
Feito: ...
Falhou / por resolver: ...
Ficheiros tocados: ...
Testes executados: comando e resultado
Próxima acção: ...
```

## Regras
- Nunca escrever «concluído» sem evidência; escrever «implementado, por validar».
- A próxima acção tem de ser tão concreta que outra pessoa a possa executar sem perguntar.
