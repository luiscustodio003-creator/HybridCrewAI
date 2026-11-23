# Relatório de testes — Fase 02 — segurança e evidências

Data: 2026-11-23 · Veredicto: **GO** para `HCW-02-012`; gate da Fase 2 **GO** em 2026-11-23T16:58:59

Tarefa: `HCW-02-012 — Consolidar segurança e evidências da Fase 2`.
Ficha: `docs/phases/phase-02.md`.
Ambiente: `.venv` do projecto; nenhuma credencial real usada. O teste real de `HCW-02-014` contactou o Ollama local em `http://127.0.0.1:11434` com `qwen3.5:4b` e está registado em `docs/reports/hcw-02-014-real.txt`.

## Comandos executados

Comandos executados na raiz do projecto com `.venv\Scripts\python.exe`:

```text
python -m pytest -q -o addopts="" tests/unit/test_ladder.py
...                                                                      [100%]
3 passed in 0.31s

python -m pytest -q -o addopts="" tests/unit/test_router_cooldown.py
...                                                                      [100%]
3 passed in 0.15s

python -m pytest -q -o addopts="" tests/unit/test_llm_contracts.py
..........                                                               [100%]
10 passed in 0.17s

python -m pytest -q -o addopts="" tests/unit/test_providers.py
.......                                                                  [100%]
7 passed in 2.74s

python -m pytest -q -o addopts="" tests/unit/test_llm_budget.py
...                                                                      [100%]
3 passed in 0.13s

python -m pytest -q -o addopts="" tests/unit/test_llm_consent.py
.....                                                                    [100%]
5 passed in 0.42s

python -m pytest -q -o addopts="" tests/unit/test_prompt_registry.py
...                                                                      [100%]
3 passed in 0.38s

python -m pytest -q -o addopts="" tests/security/test_egress.py
...                                                                      [100%]
3 passed in 0.88s

python -m pytest -q -o addopts="" tests/security/test_redaction.py
......                                                                   [100%]
6 passed in 0.12s

python -m pytest -q -o addopts="" tests/security/test_secrets.py
.........                                                                [100%]
9 passed in 0.16s

python -m pytest -q -o addopts="" tests/integration/test_llm_ping.py
....                                                                     [100%]
4 passed in 4.34s

python -m pytest -q -o addopts="" tests/integration/test_llm_real.py
ss                                                                       [100%]
2 skipped in 0.33s

python -m pytest -q -o addopts="" tests/unit/test_config.py
................                                                         [100%]
16 passed in 0.26s
```

## Resultados (passam / falham / ignorados)

### Pontos pedidos pelo Utilizador

| Ponto da Fase 2 | Ficheiro de teste | Prova executada | Resultado |
|---|---|---|---|
| Matriz de fallback | `tests/unit/test_ladder.py` | `test_gemini_para_gemini_e_automatico_e_outro_cloud_exige_autorizacao`, `test_gemini_para_ollama_so_em_tarefas_leves_e_codigo_pausa` e `test_escada_vem_de_ficheiro_e_remover_modelo_nao_muda_codigo` | **PASSA** — 3 passed |
| Timeout obrigatório | `tests/unit/test_llm_contracts.py`, `tests/unit/test_providers.py`, `tests/integration/test_llm_ping.py` | `test_timeout_tem_de_ser_positivo_e_finito` rejeita `None`, `0`, negativo, `NaN`, `inf` e `True`; `test_timeout_vira_provider_error_retryable` usa servidor lento; `test_ping_local_com_timeout_falha_sem_mostrar_segredo` falha pela CLI sem revelar o canário | **PASSA** — 10 + 13 + 5 passed |
| Egress com servidor falso | `tests/security/test_egress.py`, `tests/unit/test_providers.py`, `tests/integration/test_llm_ping.py` | `test_chave_falsa_nao_sai_em_corpo_cabecalho_nem_url` capta o pedido em `127.0.0.1`; `test_gemini_text_valida_pedido_e_payload_redigido` e `test_ping_local_contacta_ollama_falso_e_nao_reenvia_segredo` confirmam `***REDACTED***` e ausência do segredo | **PASSA** — 3 + 13 + 5 passed |
| Consentimento | `tests/unit/test_llm_consent.py`, `tests/security/test_egress.py`, `tests/integration/test_llm_ping.py` | `test_primeiro_pedido_cloud_sem_consentimento_e_acionavel_e_sem_socket`, `test_consentimento_e_tipo_de_conta_persistem_sem_credenciais`, `test_revogacao_bloqueia_pedidos_cloud_seguintes` e `test_ping_cloud_sem_consentimento_falha_sem_mostrar_segredo` | **PASSA** — 5 + 3 + 4 passed |
| Prompt injection | `tests/security/test_egress.py`, `tests/unit/test_prompt_registry.py`, `tests/security/test_redaction.py` | `test_conteudo_nao_confiavel_e_delimitado_e_marcador_forgado_e_rejeitado`, `test_bloco_nao_confiavel_entra_apenas_pelo_delimitador` e bateria de redacção com texto hostil | **PASSA** — 3 + 3 + 6 passed |
| Orçamento de ferramentas | `tests/unit/test_llm_budget.py` | `test_exceder_limite_gera_erro_tipado_e_evento_antes_da_chamada`, `test_ollama_recebe_lista_curta_com_descricoes_breves` e `test_estimativa_de_tokens_e_deterministica_e_sem_fornecedor` | **PASSA** — 3 passed |
| Endereços em configuração | **sem teste** | `tests/unit/test_config.py` valida caminhos, nível de log, `cloud_enabled`, ausência de chave de API e `HCW_OLLAMA_MODEL`, mas não carrega nem valida `gemini_text_endpoint`, `gemini_live_endpoint` nem `ollama_endpoint`. Os endereços só entram por `--endpoint` ou construtor dos adaptadores. | **PARCIAL** — endereços continuam sem teste; modelo Ollama coberto em `HCW-02-014` |
| Caminho e corpo Ollama | `tests/unit/test_config.py`, `tests/unit/test_providers.py`, `tests/integration/test_llm_ping.py` | `test_modelo_ollama_e_lido_da_configuracao`, `test_modelo_configurado_e_a_unica_origem_do_corpo`, `test_ollama_sem_modelo_configurado_falha_antes_de_conectar`, `test_ollama_rejeita_evento_de_streaming`, `test_ollama_rejeita_ndjson_como_resposta_unica` e `test_ping_local_sem_modelo_configurado_falha_com_mensagem_clara` | **PASSA** — 19 + 13 + 5 passed |

### Restantes pontos da ficha

| Ponto da ficha | Ficheiro de teste | Prova executada | Resultado |
|---|---|---|---|
| `llm/contracts` | `tests/unit/test_llm_contracts.py` | Imutabilidade, tipo explícito de fornecedor, timeout finito, redacção em `repr`/`str` e `ProviderError` tipado | **PASSA** — 10 passed |
| `providers` (`gemini_live`, `gemini_text`, `ollama`) | `tests/unit/test_providers.py` | Servidor HTTP falso rigoroso, `POST /api/generate`, corpo restrito, recusa de `provider` errado, timeout, consentimento, resposta inválida e contrato `LiveSession` | **PASSA** — 13 passed |
| `router` (`ladder`, `cooldown`, `errors`) | `tests/unit/test_router_cooldown.py`, `tests/unit/test_ladder.py` | Classificação separada de timeout/429/resposta inválida, retries limitados, cooldown por tipo e escada configurável | **PASSA** — 3 + 3 passed |
| `budget` (`tokens`, `tools_budget`) | `tests/unit/test_llm_budget.py` | Estimativa determinística, `BudgetExceeded` com evento antes da chamada e lista curta de ferramentas | **PASSA** — 3 passed |
| `egress` (`secret_scan`, `policy`, `untrusted_wrap`) | `tests/security/test_egress.py`, `tests/security/test_redaction.py`, `tests/security/test_secrets.py` | Redacção de corpo/cabeçalhos/URL, bloqueio antes do socket e delimitadores non-forjáveis | **PASSA** — 3 + 6 + 9 passed |
| Prompts versionados em `.md` | `tests/unit/test_prompt_registry.py` | `id`, `version`, `sha256`, renderização com bloco não confiável e falha sem texto parcial | **PASSA** — 3 passed |
| ADR-0002 sem SDK externo | `tests/unit/test_providers.py` | `test_adaptadores_nao_importam_sdk_externo` procura `litellm`, `google.genai`, `import ollama` e `import requests` nos adaptadores | **PASSA** — incluído nos 7 passed |
| Timeout, 429 e resposta inválida | `tests/unit/test_router_cooldown.py`, `tests/unit/test_providers.py` | `test_timeout_http_429_e_resposta_invalida_sao_classificados_a_parte`, `test_retries_sao_limitados_e_jitter_pode_ser_desactivado` e `test_resposta_invalida_vira_erro_sem_contexto` | **PASSA** — 3 + 7 passed |
| Testes reais Gemini/Ollama | `tests/integration/test_llm_real.py` | Os testes existem, mas são ignorados sem `HCW_GEMINI_TEXT_ENDPOINT` / `HCW_OLLAMA_ENDPOINT` e sem nome real de modelo em `HCW_OLLAMA_MODEL` | **IGNORADOS** — 2 skipped; não provam resposta real neste ambiente |
| Demonstração `hcw llm ping` | `tests/integration/test_llm_ping.py` | Modo simulado, servidor falso local, falha sem modelo configurado, negação cloud e timeout sem segredo na saída | **PASSA** — 5 passed |
| Gate: matriz de fallback completa | `tests/unit/test_ladder.py` | Ver linha da matriz de fallback | **PASSA** — 3 passed |
| Gate: zero segredos no payload | `tests/security/test_egress.py`, `tests/security/test_redaction.py`, `tests/security/test_secrets.py` | Canários falsos não aparecem em corpo, cabeçalhos, URL, logs, `str`/`repr` nem ficheiros | **PASSA** — 3 + 6 + 9 passed |
| Gate: quotas e orçamento a funcionar | `tests/unit/test_llm_budget.py`, `tests/unit/test_router_cooldown.py` | Limite de tokens, selecção de ferramentas, retries limitados e cooldown por tipo de erro | **PASSA** — 3 + 3 passed |

## Critérios de aceitação — HCW-02-012

| Critério | Evidência | Resultado |
|---|---|---|
| Relatório apresenta matriz de fallback, zero segredos no payload, quotas activas e consentimento verificado | Secção «Resultados» deste relatório, com ficheiros, nomes de teste e contagens reais | **PASSA** |
| `THREAT_MODEL.md` regista ameaças de egress, prompt injection e falha de fornecedor com testes correspondentes | Linhas actualizadas em `THREAT_MODEL.md` com `tests/security/test_egress.py`, `tests/unit/test_prompt_registry.py` e `tests/unit/test_router_cooldown.py` | **PASSA** |
| Evidências citam comandos executados e ficheiros reais, sem afirmar validação sem teste | Secção «Comandos executados» e coluna «Ficheiro de teste»; ponto sem teste está marcado como **SEM TESTE** | **PASSA** |

## Evidências

- `docs/reports/phase-02-security.md` — este relatório.
- `THREAT_MODEL.md` — ameaças da Fase 2 ligadas a testes concretos.
- `docs/MAP.md` — índice actualizado com a matriz e a lacuna detectada.
- `docs/reports/hcw-02-013.md` — evidência da correcção de `ProviderError`.
- `docs/reports/hcw-02-014.md` — evidência do adaptador Ollama, configuração do modelo e redacção segura do corpo.
- `reports/phase-02/report.md` — resultado anterior do `run_gate.py --phase 2`, gerado antes da validação de `HCW-02-012`; será regenerado após autorização explícita.

## Problemas pendentes e limitações conhecidas

- **Lacuna sem teste:** endereços dos fornecedores não são carregados pela configuração. `Settings` em `app/core/config/schema.py` não tem campos de endpoint e `load_settings()` em `app/core/config/loader.py` não lê variáveis de endpoint. Só `--endpoint` da CLI e os construtores dos adaptadores fornecem URLs, ambos já validados por `validar_endpoint()`.
- **Limitação parcial:** endereços Gemini continuam sem ser lidos de `Settings`; `HCW-02-014` cobre `HCW_OLLAMA_MODEL`, o caminho `/api/generate` e o corpo restrito, sem inventar URLs.
- **Tarefa A implementada:** `HCW-02-013 — Corrigir ProviderError para excepção normal`, estado `IMPLEMENTED`, evidência em `docs/reports/hcw-02-013.md`. A excepção é normal, a auditoria não encontrou outras excepções frozen em `app/` e a suíte completa passou sem alterar o comportamento de redacção.
- **Tarefa B validada:** `HCW-02-014 — Corrigir adaptador Ollama e tornar modelo configurável`, estado `VALIDATED`, evidência em `docs/reports/hcw-02-014.md` e `docs/reports/hcw-02-014-real.txt`. Caminho, corpo, resposta e streaming foram confirmados em `https://docs.ollama.com/api/generate`; a recusa de caminhos errados no servidor falso, `HCW_OLLAMA_MODEL`, a rejeição de NDJSON e a redacção segura do corpo estão cobertas por testes. O teste real com `qwen3.5:4b` passou com timeout de 900 s (`896,82 s`), sem alterar o corpo restrito; o modelo tem `thinking default true` e a margem é estreita.
- **Correcção de egress:** `redact_body()` redige valores string antes de `json.dumps`; a redacção do JSON já serializado foi removida porque corrompia o corpo e mascarava a falha real.
- **Gate GO, etiqueta por corrigir:** `python scripts/run_gate.py --phase 2` devolveu `GO` em 2026-11-23T16:58:59. A etiqueta `phase-02-go` já existia em `6c0ecf7` (`HCW-02-011`); não foi movida nem houve push. As alterações de `HCW-02-012` a `HCW-02-014` ficam sem commit nesta sessão.
- **Testes reais opcionais:** o teste Ollama em `tests/integration/test_llm_real.py` passou com `qwen3.5:4b` e timeout de 900 s; Gemini continua skipped por falta de endpoint/credencial. Só Ollama é evidência de resposta real concluída.
- **Timeout:** o contrato `ModelRequest` e todas as chamadas do gateway passam `timeout_s`; `EgressPolicy.send_json()` mantém um valor por omissão para uso directo, mas não é usado sem timeout pelos adaptadores. Não existe guarda AST global que falhe se uma futura chamada `urlopen` omitir o argumento.
- **Fora do pedido:** a ficha menciona `feature flag: gateway`, mas não há uma chave de activação implementada; esta consolidação não a trata como entrega funcional testável.

## Veredito

`HCW-02-012` está **VALIDADA** com `validated_on: 2026-11-23`: relatório, modelo de ameaças e mapa estão actualizados com evidência real. `tests/security/test_egress.py` → `3 passed`.

O gate da Fase 2 correu com autorização explícita e devolveu `GO` em 2026-11-23T16:58:59. A etiqueta `phase-02-go` já existia num commit anterior (`6c0ecf7`) e não foi reposicionada; movê-la ou criar commits/push exige autorização explícita. `HCW-02-014` está validada com servidor falso e com teste real contra Ollama local.
