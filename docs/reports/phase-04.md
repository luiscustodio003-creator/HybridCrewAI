# Relatório final — Fase 04

Data: 2026-11-26 · Gate: EM EXECUÇÃO · Depende de HCW-04-012.

## O que foi feito (por tarefa)

HCW-04-001 — identificados os fluxos e limites do MVP.
HCW-04-002 — consolidado o contrato do caso dourado.
HCW-04-003 — definidos os limites da guarda de subprocesso.
HCW-04-004 — implementado o contrato de saída dos agentes.
HCW-04-005 — implementada a validação de conteúdo não confiável.
HCW-04-006 — implementado o emissor de tokens opacos.
HCW-04-007 — implementada a interface local de aprovação.
HCW-04-008 — executado o caso dourado da calculadora.
HCW-04-009 — implementada a retoma verificável do fluxo CREATE.
HCW-04-010 — concluída a interface local de equipa e aprovação.
HCW-04-011 — executado o harness com cinco casos e pontuação.

## Casos de referência

| Caso | Descrição | Obrigatório | Estado |
|---|---|---|---|
| golden_calculadora | Calculadora ponta a ponta | sim | PASSA |
| aprovacao_obrigatoria | Aprovação só por token válido | não | PASSA |
| approved_claim_nao_aprova | Claim do modelo não aprova | não | PASSA |
| saida_invalida_limitada | Saída inválida com limites | não | PASSA |
| retomada_idempotente | Retoma sem repetir passos | não | PASSA |

Pontuação: 5/5 · Mínimo: 4 · Dourado: PASSA · Resultado: APROVADO

## Verificações

| Caso | Verificação | Estado | Detalhe |
|---|---|---|---|
| golden_calculadora | fluxo ponta a ponta | PASSA | — |
| golden_calculadora | execução capturada | PASSA | — |
| aprovacao_obrigatoria | paragem antes da aprovação | PASSA | — |
| aprovacao_obrigatoria | token de outra tarefa recusado | PASSA | — |
| aprovacao_obrigatoria | diff alterado recusado | PASSA | — |
| aprovacao_obrigatoria | executor recusa sem token válido | PASSA | — |
| approved_claim_nao_aprova | claim observado na saída | PASSA | — |
| approved_claim_nao_aprova | estado continua pendente | PASSA | — |
| approved_claim_nao_aprova | sem evento de aprovação | PASSA | — |
| approved_claim_nao_aprova | resultado DONE | PASSA | — |
| saida_invalida_limitada | repetição única | PASSA | — |
| saida_invalida_limitada | resultado final DONE | PASSA | — |
| saida_invalida_limitada | marcador forjado recusado | PASSA | — |
| saida_invalida_limitada | sem repetição no marcador | PASSA | — |
| retomada_idempotente | retoma concluída | PASSA | — |
| retomada_idempotente | último passo RELATORIO | PASSA | — |
| retomada_idempotente | chamadas restantes | PASSA | — |
| retomada_idempotente | eventos encadeados | PASSA | — |
| retomada_idempotente | hash do token persistido | PASSA | — |

## Comandos executados

1. `python -m pytest -q tests/eval/test_reference_cases.py tests/unit/test_final_report.py`
2. `python -m tests.eval.runner --saida reports/tasks/HCW-04-011-avaliacao.json`
3. `python -m pytest -q --deselect tests/ui/test_browser.py::test_evidencia_real_no_browser`
4. `python -m ruff check tests/eval tests/unit/test_final_report.py reports/final_report.py`
5. `python -m ruff format --check tests/eval tests/unit/test_final_report.py reports/final_report.py`
6. `python -m mypy --explicit-package-bases tests/eval/cases.py tests/eval/scorer.py tests/eval/runner.py tests/eval/test_reference_cases.py tests/unit/test_final_report.py reports/final_report.py`
7. `python scripts/check_file_size.py`
8. `python scripts/validate_plan.py`
9. `python scripts/check_traceability.py`
10. `python scripts/check_modules.py`
11. `python scripts/plan_status.py`
12. `python -m reports.final_report --avaliacao reports/tasks/HCW-04-011-avaliacao.json --metadados reports/tasks/HCW-04-011-metadados.json --saida docs/reports/phase-04.md`

## Resultados (passam / falham / ignorados)

| Verificação | Resultado |
|---|---|
| harness | 10 passed |
| regressao_focada | 44 passed |
| regressao_ampla | 307 passed, 2 skipped, 1 deselected |
| ruff | 0 errors |
| ruff_format | 9 files already formatted |
| mypy | 0 issues |
| check_file_size | 0 errors, 22 warnings |
| validate_plan | 0 errors, 0 warnings |
| check_traceability | 0 errors, 0 warnings |
| check_modules | 0 errors, 0 warnings |

## Critérios de aceitação (um por linha, com a prova)

- [x] Cinco casos de referência são pontuados e o caso dourado é obrigatório.
- [x] Pontuação mínima é 4 em 5 e o relatório final inclui comandos, resultados e digests.
- [x] Relatório não contém segredos, token real ou prompt completo.

## Evidências

| Nome | Digest/valor |
|---|---|
| diff_hash | `cc1631c25d9fe07728b20012b719d4692ef775b99b3a6464f15d3a5d922c4e21` |
| token_hash | `f789d7fde3fa7a3283bae562890f99bf3b006ba29a5e370dd85d69024615ce72` |
| stdout_sha256 | `99cef98de12a8b8a90abbcb2033d076bfc563ea7951d4da90263da27288d16f6` |
| relatorio_sha256 | `b2779a4718dcf65330c83a2de96faafb3224417b4778dfe0d61601c0541592e5` |
| digest_casos | `6934e53982ec6436e9c11dc407b44920ec82ffe364c00635b2e5fb8661e91bd9` |
| captura_equipa_sha256 | `2fcb7d9ee3ae950a72c1520bb6ece55cb4b7a62fa05fb84f1a7b7760f7898658` |
| captura_aprovacao_sha256 | `4fe88396458a0a36d072606e8ac58d0e621f133ec53110a0377cf4afab91e655` |

## Decisões tomadas (ADR e IDs)

- ADR-004 — aprovação apenas por token opaco emitido pela UI local.
- ADR-005 — saída do modelo tratada como dado não confiável.
- ADR-006 — checkpoints com chaves de idempotência por passo.

## Limitações conhecidas

- O executor é não isolado; a guarda reduz ficheiros e rede, mas não é uma sandbox.
- Os fornecedores de modelo nos testes são determinísticos e locais (ProviderKind.FAKE).
- A falha pre-existente em tests/ui/test_browser.py::test_evidencia_real_no_browser foi deseleccionada na regressao.
- A captura 02-aprovacao.png foi actualizada nesta sessao e o digest usado e o actual.

## Ideias adiadas (IDEA-xxx)

- Nenhuma ideia registada nesta tarefa.

## Como demonstrar (passos para um agente novo)

1. Ler `tasks.yaml`, `STATE.md` e `docs/requirements.yaml`.
2. Rodar `python -m pytest -q tests/eval/test_reference_cases.py`.
3. Rodar o gate com `--deselect tests/ui/test_browser.py::test_evidencia_real_no_browser`.
4. Comparar os digests acima com a saída dos testes.
5. Ler `docs/reports/phase-04-security.md` para a consolidação HCW-04-012 das ameaças e da não-exposição de segredos.
