# Modelo de ameaças
Cada ameaça liga-se a uma fase e a um teste que a ataca de facto (Skill `hcw-security-review`).

| Ameaça | Fase | Contramedida | Teste |
|---|---|---|---|
| Prompt injection em ficheiros, páginas ou binários | 2, 7, 13 | Conteúdo como dados delimitados; agentes sem ferramentas directas; marcador de fecho não forjável | `tests/security/test_egress.py::test_conteudo_nao_confiavel_e_delimitado_e_marcador_forgado_e_rejeitado` e `tests/unit/test_prompt_registry.py::test_bloco_nao_confiavel_entra_apenas_pelo_delimitador` — PASSA (3+3) |
| Fuga de segredos para a cloud | 2, 5 | Scan, redacção e exclusão antes do envio; interruptor por projecto | `tests/security/test_egress.py::test_chave_falsa_nao_sai_em_corpo_cabecalho_nem_url` e `tests/integration/test_llm_ping.py::test_ping_local_contacta_ollama_falso_e_nao_reenvia_segredo` — PASSA (3+4) |
| Falha de fornecedor (timeout, 429, resposta inválida) | 2 | Classificação por tipo, retries limitados, cooldown separado e erro sem contexto sensível | `tests/unit/test_router_cooldown.py::test_timeout_http_429_e_resposta_invalida_sao_classificados_a_parte`, `tests/unit/test_providers.py::test_resposta_invalida_vira_erro_sem_contexto`, `tests/unit/test_llm_contracts.py::test_provider_error_atravessa_contextmanager` e `test_outras_excecoes_nao_sao_dataclasses_frozen` — PASSA (3+7+2); `HCW-02-013` implementada |
| Endereços de fornecedores ausentes da configuração | 2 | Endereços completos por configuração/construtor; nunca inventar URLs por omissão | **PARCIAL** — `Settings` não tem campos de endpoint; `HCW-02-014` implementou `HCW_OLLAMA_MODEL`, `POST /api/generate` e corpo restrito com servidor falso, mas endereços Gemini continuam por configurar e o teste real com modelo de `ollama list` está pendente |
| Aprovação forjada pelo modelo | 4, 12 | Token único emitido só pela interface, ligado ao hash do diff | Agente devolve approved=true sem efeito |
| ZIP malicioso (Zip Slip, bomb, symlinks) | 5 | Limites, validação de caminhos, quarentena | Arquivos hostis em fixtures |
| Path traversal e symlinks exteriores | 5 | Canonicalização; workspace como unidade de permissões | Bateria de caminhos |
| Execução de código gerado ou de terceiros | 4, 6 | Isolamento obrigatório; recusa sem mecanismo seguro; sem rede nem credenciais | Testes de fuga |
| Injecção de comandos em ferramentas | 12 | Parâmetros tipados, sem shell, sem código escrito pelo modelo | Nomes com & ; | |
| Fecho do processo ou janela errada | 12 | Correspondência por processos em execução; protecção do próprio assistente | Teste de auto-protecção |
| Interface local atacada via browser | 3 | 127.0.0.1, token de sessão, verificação de Origin | Pedidos com Origin falso |
| Dependência ou ferramenta comprometida | 0, 13 | Versões fixadas, pip-audit, origens oficiais, instalação com aprovação | Verificação no CI |
| Perda de trabalho em falhas | 1, 5, 9 | Snapshots, checkpoints, testes de kill | Testes de recuperação |
| Custos e quotas fora de controlo | 2, 9 | Orçamento por tarefa, pausa por quota, botão de paragem | `tests/unit/test_llm_budget.py::test_exceder_limite_gera_erro_tipado_e_evento_antes_da_chamada` e `tests/unit/test_llm_contracts.py::test_timeout_tem_de_ser_positivo_e_finito` — PASSA (3+10) |
| Acção reportada como feita sem o ter sido | 1, 12 | ToolResult com verificação; unverified nunca é sucesso | Aplicação inexistente |
