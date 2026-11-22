---
name: hcw-implement
description: Implementa UMA tarefa aprovada do HybridCrewAI com alteração mínima, ficheiros pequenos e testes. Usar quando o utilizador pedir para implementar, codificar, criar um módulo, corrigir ou refactorizar uma tarefa HCW-XX-NNN, ou quando o hcw-phase-runner chegar a uma tarefa APPROVED. Aplica as regras de código do projecto.
---

# Implementar uma tarefa

## Antes de escrever código
1. Confirmar: a tarefa está `APPROVED` e as dependências estão concluídas. Senão, parar.
2. Marcar `IN_PROGRESS` em `tasks.yaml`.
3. Ler os módulos envolvidos, os testes existentes e quem os consome. Reutilizar antes de criar.
4. Ler `references/CODING_RULES.md` (curto).

## Escrever
5. **Teste primeiro** quando possível: escrever o teste que falha, depois o código.
6. Alteração mínima coerente; uma tarefa não mexe em áreas independentes.
7. Respeitar os contratos do plano: `ToolResult` nas ferramentas, aprovação só por token da UI, conteúdo externo como dados.
8. Por cada pasta nova de módulo: `README.txt` e `module.yaml` (modelos em `hcw-docs`).

## Verificar
9. `python -m pytest -q <testes da tarefa>`, depois a regressão relevante.
10. `ruff check .` e `python scripts/check_file_size.py`.
11. Se falhar 3 vezes pelo mesmo motivo: parar, marcar `BLOCKED`, descrever o problema e pedir decisão.
12. Passar a tarefa a `IMPLEMENTED`; a validação final é do `hcw-test-gate`.

## Nunca
- Inventar APIs ou versões: confirmar na documentação oficial ou no código instalado.
- Executar código gerado fora do ambiente autorizado; instalar dependências sem aprovação.
- Tocar em ficheiros fora da tarefa «já que estava ali».
