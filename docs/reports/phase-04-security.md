# Segurança da Fase 4

Data: 2026-11-26 · Tarefa: HCW-04-012 · Veredicto: GO

## Comandos executados

1. `python -m pytest -q tests/security/test_phase04_threats.py` → 5 testes passaram.
2. `python -m pytest -o addopts="" --tb=no -q tests/eval/test_reference_cases.py tests/unit/test_final_report.py tests/security/test_phase04_threats.py tests/security/test_simple_runner.py tests/security/test_approval_tokens.py tests/unit/test_simple_runner.py` → `30 passed in 4.39s`.
3. `python -m pytest -o addopts="" --tb=no -q --deselect tests/ui/test_browser.py::test_evidencia_real_no_browser` → `312 passed, 2 skipped, 1 deselected in 49.41s`.
4. `python -m ruff check tests/security/test_phase04_threats.py` → `All checks passed!`.
5. `python -m ruff format --check tests/security/test_phase04_threats.py` → `1 file already formatted`.
6. `python -m mypy --explicit-package-bases tests/security/test_phase04_threats.py` → `Success: no issues found in 1 source file`.
7. `python scripts/check_file_size.py` → `[OK] 0 erro(s), 22 aviso(s)`.
8. `python scripts/validate_plan.py` → `[OK] 0 erro(s), 0 aviso(s)`.
9. `python scripts/check_traceability.py` → `[OK] 0 erro(s), 0 aviso(s)`.
10. `python scripts/check_modules.py` → `[OK] 0 erro(s), 0 aviso(s)`.
11. `python scripts/plan_status.py` → Fase 4 `12/13`; próxima tarefa `HCW-04-999`.
12. `python scripts/run_gate.py --phase 4` → `NO-GO`; detalhe em `reports/phase-04/report.md`.

## Ameaças ligadas a testes reais

| Ameaça | Contramedida | Prova executada | Resultado |
|---|---|---|---|
| Prompt injection em ficheiros, páginas e chat | Conteúdo tratado como dado, marcador de fecho não forjável e cliente com `textContent` | `tests/security/test_egress.py::test_conteudo_nao_confiavel_e_delimitado_e_marcador_forgado_e_rejeitado`, `tests/integration/test_ui_chat.py::test_prompt_versionado_delimita_conteudo_do_utilizador`, `tests/ui/test_browser_phase04.py::test_evidencia_equipa_e_aprovacao_no_browser` | PASSA |
| Aprovação forjada pelo modelo | Token opaco ligado a tarefa, correlação e diff; claim do modelo não altera estado | `tests/unit/test_agent_runner.py::test_aprovacao_reivindicada_pelo_modelo_nao_altera_estado`, `tests/security/test_approval_tokens.py::test_saida_do_modelo_com_approved_true_nao_emite_token`, `tests/integration/test_create_golden.py::test_caso_dourado_calculadora_ponta_a_ponta` | PASSA |
| Reexecução duplicada ou perda de checkpoint | Idempotência confirmada após sucesso e checkpoint SQLite com digests opacos | `tests/unit/test_create_workflow.py::test_chave_repetida_nao_duplica_eventos_nem_avanca_estado`, `tests/integration/test_create_workflow_checkpoint.py::test_checkpoint_sobrevive_a_reinicio_sem_repetir_passos`, `tests/recovery/test_create_kill_resume.py::test_kill_e_retoma_create_sem_repetir_passo_confirmado` | PASSA |
| Execução de código gerado ou de terceiros | Executor simples explicitamente não isolado, sem shell, token obrigatório, guarda de ficheiros/rede para Python e prazo/cancelamento | `tests/security/test_phase04_threats.py::test_executor_nao_isolado_recusa_sem_token_valido`, `::test_documentacao_declara_executor_nao_isolado`, `tests/security/test_simple_runner.py::test_subprocesso_sem_rede_e_sem_segredes`, `tests/unit/test_simple_runner.py::test_execucao_sem_token_valido_e_recusada` | PASSA |
| Interface local atacada via browser | Servidor em loopback, token em memória, `Origin` e `Sec-Fetch-Site` verificados | `tests/security/test_ui_local.py::test_pedido_sem_token_devolve_401_e_nao_executa_rota`, `::test_origin_fora_do_loopback_devolve_403`, `tests/ui/test_browser_phase04.py::test_evidencia_equipa_e_aprovacao_no_browser` | PASSA |
| Cliente web com recursos externos, XSS ou token persistido | Whitelist local, CSP restrita, `textContent`, token apenas em memória | `tests/unit/test_ui_web_assets.py::test_recursos_nao_tem_urls_externas`, `::test_scripts_nao_injetam_html_nem_guardam_token`, `tests/security/test_ui_approvals.py::test_html_nao_contem_token` | PASSA |
| Relatório final expor segredo, token real ou prompt completo | Digests allowlistados, nomes curtos e filtro de valores sensíveis | `tests/security/test_phase04_threats.py::test_relatorios_da_fase_4_nao_expoem_segredos_nem_prompt`, `::test_modelo_de_ameacas_da_fase_4_liga_ameacas_a_testes_reais`, `tests/unit/test_final_report.py::test_relatorio_filtra_valores_sensiveis_e_digests_invalidos` | PASSA |

## Critérios de aceitação

| Critério | Prova | Resultado |
|---|---|---|
| Cada ameaça da Fase 4 em `THREAT_MODEL.md` aponta para teste real com `PASSA` | `test_modelo_de_ameacas_da_fase_4_liga_ameacas_a_testes_reais` percorre as linhas da fase 4 e exige `tests/`, `test_` e `PASSA` | PASSA |
| Executor não isolado documentado e apenas com token válido | `test_executor_nao_isolado_recusa_sem_token_valido`, `test_documentacao_declara_executor_nao_isolado` e `execution/README.txt` | PASSA |
| Nenhum segredo real, token real ou prompt completo em ficheiros, logs ou relatórios | `test_relatorios_da_fase_4_nao_expoem_segredos_nem_prompt` verifica relatórios, modelo de ameaças e prompt versionado | PASSA |

## Evidências

- `THREAT_MODEL.md` — nova linha liga a exposição de segredos no relatório a testes reais.
- `tests/security/test_phase04_threats.py` — cinco testes de consolidação da Fase 4, todos passaram.
- `execution/README.txt` — executor descrito como não isolado e novo teste listado.
- `execution/module.yaml` — lista de testes actualizada.
- `docs/MAP.md` — mapa actualizado com a consolidação de segurança.
- `docs/reports/phase-04.md` — referência ao relatório de segurança.
- `reports/tasks/HCW-04-012.md` — relatório da tarefa com comandos, resultados e gate.
- `reports/phase-04/report.md` e `reports/phase-04/report.json` — gate NO-GO com as falhas do pytest cumulativo.

## Limitações conhecidas

- O executor simples é não isolado; a guarda reduz ficheiros e rede, mas não cobre binários nativos arbitrários.
- O gate da Fase 4 ficou NO-GO por `tests/ui/test_browser.py::test_evidencia_real_no_browser` e por uma falha de ligação em `tests/integration/test_ui_approvals.py::test_post_approvals_recusa_pedidos_invalidos[cabecalhos1-corpo1-403]` na execução cumulativa; ambos precisam de tarefa aprovada para correcção.
- A suíte completa com o teste de browser deseleccionado passou: `312 passed, 2 skipped, 1 deselected`.
- `ruff check .` global e `HCW-00-006` mantêm erros pré-existentes em `scripts/`; a verificação foi feita nos ficheiros tocados.
- O gate depende de `HCW-04-999`, de `phase-04-start` e de autorização explícita para criar `phase-04-go`.
- Nenhum segredo real, token real ou prompt completo foi escrito em ficheiro, log ou Git.
