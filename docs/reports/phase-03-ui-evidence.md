# Evidência real de interface — Fase 3

Data: 2026-11-24 · Tarefa: HCW-03-010 · Veredicto: **GO**

## Objectivo

Produzir evidência executável da interface web local em Chromium real: eventos no ecrã, filtros, chamadas LLM, chat, capturas de ecrã e ausência de pedidos externos ou persistência de token.

## Comandos executados

```
.venv\Scripts\python.exe -m pytest -o addopts="" -q tests/ui/test_browser.py
Failed: Playwright não instalado: execute python -m pip install playwright==1.65.2 e depois python -m playwright install chromium.
```

Estado vermelho confirmado antes da implementação, de acordo com a regra de teste primeiro.

```
.venv\Scripts\python.exe -m pip install playwright==1.65.2
Successfully installed greenlet-3.5.6 playwright-1.65.2

.venv\Scripts\python.exe -m playwright install chromium
Chrome for Testing 159.0.8154.6 (playwright chromium v1255) descarregado para C:\Users\DELL\AppData\Local\ms-playwright\chromium-1255.
```

```
.venv\Scripts\python.exe -m pytest -o addopts="" -q tests/ui/test_browser.py
1 passed in 4.20s

.venv\Scripts\python.exe -m pytest -o addopts="" -q
214 passed, 2 skipped in 41.89s

.venv\Scripts\ruff.exe check tests/ui/test_browser.py
All checks passed!

.venv\Scripts\mypy.exe tests/ui/test_browser.py
Success: no issues found in 1 source file

.venv\Scripts\python.exe scripts/validate_plan.py
[OK] validate_plan: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_traceability.py
[OK] check_traceability: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_modules.py
[OK] check_modules: 0 erro(s), 0 aviso(s)

.venv\Scripts\python.exe scripts/check_file_size.py
[OK] check_file_size: 0 erro(s), 8 aviso(s)
```

## Critérios de aceitação

| Critério | Prova | Resultado |
|---|---|---|
| Playwright e browser local ficam fixados em `requirements.lock.txt` após aprovação explícita | `playwright==1.65.2` e a dependência transitiva `greenlet==3.5.6` foram adicionados ao bloqueio UTF-16 LE; o browser real foi instalado e usado no teste | PASSA |
| Teste real verifica evento no ecrã em menos de 1 s, filtros e envio de mensagem no chat | `test_evidencia_real_no_browser` usa Chromium headless, mede `time.perf_counter()` até `#eventos` mostrar o marcador e compara com `_LIMIAR_LATENCIA_S = 1.0`; filtra por `correlation_id` e nível, filtra chamadas LLM e envia mensagem com `correlation_id` e `task_id` | PASSA |
| Capturas de ecrã reais são gravadas em `screenshots/phase-03` e citadas no relatório | `01-eventos.png` e `02-chat.png` foram gravadas pelo browser real durante o teste; tamanhos e SHA-256 estão registados abaixo | PASSA |
| Sem browser instalado o teste falha com mensagem clara e nunca é marcado como PASSA | Antes da instalação, o teste falhou com instrução explícita; a importação opcional e a excepção de arranque do Chromium chamam `pytest.fail` com comandos de reparação | PASSA |

## Segurança observada no browser

| Verificação | Resultado |
|---|---|
| Nenhum pedido para origem externa; URLs iniciadas pela página analisadas uma a uma | PASSA |
| Token falso apenas em memória, nunca no URL nem em pedidos externos | PASSA |
| `localStorage` e `sessionStorage` vazios após a interação | PASSA |
| Servidor real apenas em `127.0.0.1`, com token Bearer e validação de origem local | PASSA |

## Capturas

| Ficheiro | Bytes | SHA-256 |
|---|---:|---|
| `screenshots/phase-03/01-eventos.png` | 55013 | `bcdab2aba6c4de840b20e74e27ddb0c4c0a1c8c5936d7d6c8e3b4d33ddd8d4ad` |
| `screenshots/phase-03/02-chat.png` | 57659 | `3ba5395120f0da9af5c0afa2354085505907d9de73686d61e965d12cc76f7541` |

## Evidências

- `tests/ui/test_browser.py` — teste real com servidor local efémero, Chromium headless e quatro painéis.
- `requirements.lock.txt` — versões fixadas de Playwright e da dependência transitiva.
- `screenshots/phase-03/01-eventos.png` — painel de eventos com filtro aplicado.
- `screenshots/phase-03/02-chat.png` — painel de chat após envio de mensagem.
- `reports/tasks/HCW-03-010.md` — relatório de validação da tarefa.

## Problemas pendentes e limitações conhecidas

- A ramificação para Chromium ausente está implementada, mas não foi simulada depois da instalação; a falha clara foi observada com Playwright ausente.
- O token continua a ter de ser introduzido novamente após recarregar a página; isso é uma decisão de segurança das fases anteriores.
- Nenhum segredo real foi usado: o teste emprega apenas o token falso `token-falso-ui`, que não é credencial de acesso.
- `check_file_size.py` continua com avisos pré-existentes; `tests/ui/test_browser.py` tem 298 linhas e respeita o limite de 300.
