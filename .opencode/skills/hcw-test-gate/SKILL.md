---
name: hcw-test-gate
description: Valida tarefas e fecha fases do HybridCrewAI com testes reais e evidência. Usar quando o utilizador pedir testar, validar, fechar a tarefa, "passou o gate", correr hcw accept, ver o relatório, ou antes de marcar qualquer tarefa como VALIDATED. Decide GO ou NO-GO e nunca aceita a palavra do agente como prova.
---

# Testes e gates

## Validar uma tarefa
1. Correr os testes listados na tarefa e depois a regressão relevante; guardar a saída.
2. Confirmar um a um os `acceptance`. Se algum não tiver teste que o prove, a tarefa **não** passa.
3. Só então: `status: VALIDATED`, `validated_on` com a data e `evidence` com os caminhos reais (relatórios, capturas, logs).
4. `python scripts/validate_plan.py` e `python scripts/check_traceability.py`.

## Gate da fase
1. Todas as tarefas da fase (menos o gate) em `IMPLEMENTED` ou `VALIDATED`.
2. `python scripts/run_gate.py --phase N` (corre guardas, testes acumulados de todas as fases até N e escreve `reports/phase-NN/`).
3. `GO`: validar as tarefas com o relatório como evidência, marcar o gate `VALIDATED`, etiquetar `git tag phase-NN-go`.
4. `NO-GO`: ler `reports/phase-NN/report.md`, corrigir a causa (não o teste, salvo se o teste estiver errado e isso for explicado), repetir.

## Regras de teste
- Real por defeito: SQLite, ficheiros, processos e servidor reais. Mocks só para falhas de fornecedores e para o que custa dinheiro.
- Testes com Gemini real são opcionais e só com autorização (`live_cloud`).
- Cada ataque do `THREAT_MODEL.md` da fase tem um teste que o tenta de facto.
- Usar `templates/TEST_REPORT_TEMPLATE.md` para o relatório de fase.
