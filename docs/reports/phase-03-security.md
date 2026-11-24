# Segurança da Fase 3

Data: 2026-11-24 · Tarefa: HCW-03-011 · Veredicto: **GO**

## Comandos executados

```
.venv\Scripts\python.exe -m pytest -o addopts="" -q tests/security/test_ui_local.py
1 failed, 10 passed in 6.91s
```

Estado vermelho confirmado: o relatório de segurança da Fase 3 ainda não existia.

```
.venv\Scripts\python.exe -m pytest -o addopts="" -q tests/security/test_ui_local.py
11 passed in 6.35s

.venv\Scripts\python.exe -m pytest -o addopts="" -q
216 passed, 2 skipped in 43.56s

.venv\Scripts\ruff.exe check tests/security/test_ui_local.py
All checks passed!

.venv\Scripts\mypy.exe tests/security/test_ui_local.py
Success: no issues found in 1 source file

.venv\Scripts\python.exe scripts/validate_plan.py
[OK] validate_plan: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_traceability.py
[OK] check_traceability: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_modules.py
[OK] check_modules: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_file_size.py
[OK] check_file_size: 0 erro(s), 9 aviso(s)
```

## Ameaças ligadas a testes reais

| Ameaça | Contramedida | Prova executada | Resultado |
|---|---|---|---|
| Pedido sem token ou com token falso | Bearer token exigido em todas as APIs e token nunca registado em logs ou respostas | `tests/security/test_ui_local.py::test_pedido_sem_token_devolve_401_e_nao_executa_rota`, `::test_events_sem_token_devolve_401`, `::test_segredos_nao_aparecem_em_logs_nem_respostas` | PASSA |
| `Origin` fora do loopback ou `Sec-Fetch-Site` cross-site | Origem aceite apenas em `http://127.0.0.1:<porta>` ou pedido de mesma origem do browser | `tests/security/test_ui_local.py::test_origin_fora_do_loopback_devolve_403`, `::test_events_com_origin_falso_devolve_403`, `tests/unit/test_ui_web_assets.py::test_origem_sem_cabecalho_aceita_apenas_mesma_origem_do_browser` | PASSA |
| Prompt injection no chat e em conteúdo externo | Prompt versionado com delimitador não forjável; cliente web usa `textContent` e não interpreta HTML | `tests/integration/test_ui_chat.py::test_prompt_versionado_delimita_conteudo_do_utilizador`, `tests/unit/test_ui_web_assets.py::test_scripts_nao_injetam_html_nem_guardam_token`, `tests/ui/test_browser.py::test_evidencia_real_no_browser` | PASSA |
| Token persistido ou pedido externo no browser | Token apenas em memória, whitelist local, CSP restrita e verificação real de URLs iniciadas pela página | `tests/ui/test_browser.py::test_evidencia_real_no_browser`, capturas `screenshots/phase-03/01-eventos.png` e `screenshots/phase-03/02-chat.png` | PASSA |

## Critérios de aceitação

| Critério | Prova | Resultado |
|---|---|---|
| `THREAT_MODEL.md` liga token, Origin, 127.0.0.1 e prompt injection a testes reais | `test_modelo_de_ameacas_da_fase_3_liga_ameacas_a_testes_reais` procura linhas com esses termos, nomes de testes e `PASSA` | PASSA |
| O relatório cita comandos executados, ficheiros e capturas sem afirmar validação sem teste | `test_relatorios_da_fase_3_documentam_evidencia_sem_segredos` exige `Comandos executados`, `tests/security/test_ui_local.py` e `screenshots/phase-03/01-eventos.png`; todas as afirmações aqui vêm de comandos registados | PASSA |
| Nenhum segredo, token real ou prompt completo aparece em relatórios, logs ou Git | O mesmo teste verifica a ausência do prompt falso e do cabeçalho Bearer nos relatórios; os testes de servidor confirmam que nem logs nem respostas os devolvem | PASSA |

## Evidências

- `THREAT_MODEL.md` — matriz actualizada com token, `Origin`, `127.0.0.1` e prompt injection ligados a testes concretos.
- `tests/security/test_ui_local.py` — dois testes novos de documentação e não-exposição de segredos.
- `docs/MAP.md` — mapa actualizado com capturas reais e relatório de segurança da Fase 3.
- `docs/reports/phase-03-ui-evidence.md` — evidência real de browser.
- `screenshots/phase-03/01-eventos.png` — 55013 bytes — SHA256 `bcdab2aba6c4de840b20e74e27ddb0c4c0a1c8c5936d7d6c8e3b4d33ddd8d4ad`.
- `screenshots/phase-03/02-chat.png` — 57659 bytes — SHA256 `3ba5395120f0da9af5c0afa2354085505907d9de73686d61e965d12cc76f7541`.
- `reports/tasks/HCW-03-010.md` — validação da evidência real de browser.

## Limitações conhecidas

- O token continua em memória e tem de ser reintroduzido após recarregar a página.
- A falha específica por Chromium ausente não foi simulada depois da instalação; a mensagem está implementada.
- Gemini, ferramentas de redes, workspace e execução isolada pertencem a fases seguintes e não foram validados aqui.
- `ruff check .` global e `HCW-00-006` continuam com erros pré-existentes em `scripts/`.
- Nenhum segredo real, token real ou prompt completo foi escrito em ficheiro, log ou Git.
