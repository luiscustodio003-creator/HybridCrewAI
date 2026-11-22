---
name: hcw-phase-runner
description: Executa uma fase completa do HybridCrewAI do princípio ao fim, documentando cada passo. Usar quando o utilizador pedir "faz a fase N", "continua o projecto", "implementa a próxima tarefa" ou "avança com o plano". Encadeia planear, aprovar, implementar, testar, documentar, gate e handoff, parando nos pontos que exigem aprovação humana.
---

# Executar uma fase

Esta Skill é o ciclo completo. Cada passo usa a Skill indicada; não saltar passos.

## Ciclo
1. **Situar** — `hcw-router`: ler `STATE.md`, correr `python scripts/plan_status.py`. Confirmar que o gate da fase anterior está `VALIDATED`; se não estiver, parar e dizê-lo.
2. **Planear** — se a fase só tem as tarefas `-001` e `-999`, usar `hcw-plan` com `docs/phases/phase-NN.md`. **Parar e pedir ao utilizador que aprove** o plano antes de continuar.
3. **Para cada tarefa `APPROVED`, por ordem de dependências:**
   1. `hcw-implement` (alteração mínima, ficheiros pequenos).
   2. `hcw-security-review` se tocar em workspace, execução, rede, credenciais ou cloud.
   3. `hcw-test-gate` ao nível da tarefa: testes específicos, depois regressão.
   4. `hcw-docs`: README.txt e `module.yaml` do módulo, entrada no `DEVLOG.md`.
   5. Actualizar o estado em `tasks.yaml` e fazer `git commit` com o ID da tarefa.
4. **Gate da fase** — `hcw-test-gate`: `python scripts/run_gate.py --phase N`. Com `NO-GO`, corrigir e repetir; nunca marcar tarefas como validadas à força.
5. **Fechar** — relatório da fase em `docs/reports/phase-NN.md` (modelo em `hcw-docs`), etiqueta `phase-NN-go`, actualizar `STATE.md`, e `hcw-handoff`.

## Pontos de paragem obrigatórios
- Aprovação do plano da fase; aprovação de qualquer ADR; qualquer operação destrutiva.
- Falha repetida (3 tentativas na mesma tarefa): parar, registar o bloqueio (`BLOCKED`) e pedir decisão.
- Decisão fora do plano: registar em `IDEAS.md` (`hcw-ideas-intake`) e não implementar.

## Porquê
O que se perde entre sessões é o contexto. Este ciclo grava o estado a cada tarefa, por isso qualquer sessão (ou outra ferramenta) retoma exactamente onde ficou.
