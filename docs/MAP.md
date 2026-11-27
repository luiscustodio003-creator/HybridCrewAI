# Mapa do projecto

Data: 2026-11-26 · Responsabilidade: DOC-001 · Estado: mapa vivo; Fases 0 a 3 encerradas, Fase 4 em fecho

Este ficheiro responde a «onde está o quê». Distingue o que existe em disco do que apenas está previsto no plano. O conteúdo dos ficheiros listados é a fonte de verdade; este mapa é um índice, não substitui os relatórios de evidência.

## Estado real

- Raiz do projecto com `app/core/`, `app/cli/` e `app/llm/` criados; o gateway tem contratos, egress, consentimento, prompts, budget, roteador e adaptadores HTTP sem SDK externo, com demonstração segura em `hcw llm ping`.
- Plano com 12 tarefas na Fase 0; 10 estão `VALIDATED`.
- Repositório Git com `origin/master` e etiqueta `phase-00-start` no commit inicial `fd9ac9c`.
- Ambiente controlado: `.venv` com Python 3.12.0; Python global 3.15.2 fora do projecto.
- CI verde em `ubuntu-latest` e `windows-latest`; evidência em `docs/reports/hcw-00-008.txt`.
- ADR-0001 aprovado: núcleo próprio, com adaptadores futuros para CrewAI e LangGraph.
- ADR-0002 aceite: gateway com contrato próprio e adaptadores finos, sem novas dependências na Fase 2.

## Responsabilidades existentes

| Responsabilidade | Pasta | Ficheiro principal | Estado |
|---|---|---|---|
| Regras globais do agente | raiz | `AGENTS.md` | existente |
| Apresentação e instalação | raiz | `README.md` | existente |
| Plano mestre e estados | raiz | `tasks.yaml` | validado por guardas |
| Continuidade da sessão | raiz | `STATE.md`, `DEVLOG.md` | existente e actualizado |
| Ideias fora do plano | raiz | `IDEAS.md` | existente |
| Modelo de ameaças | raiz | `THREAT_MODEL.md` | existente |
| Guarda de plano | `scripts/` | `validate_plan.py` | 18 testes no conjunto de scripts |
| Guarda de rastreabilidade | `scripts/` | `check_traceability.py` | sem teste directo; corrido nos gates |
| Guarda de tamanho de ficheiro | `scripts/` | `check_file_size.py` | testado |
| Guarda de módulos | `scripts/` | `check_modules.py` | testado; aviso por `app/` ainda não existir |
| Validação das Skills | `scripts/` | `lint_skills.py` | testado |
| Estado e próxima tarefa | `scripts/` | `plan_status.py` | corrido em cada handoff |
| Orquestração do gate | `scripts/` | `run_gate.py` | a usar no `HCW-00-999` |
| Auxiliar partilhado | `scripts/` | `_common.py` | testado indirectamente |
| Testes dos guardas | `tests/scripts/` | `test_*.py` | 18 passaram no `.venv` |
| Fichas das fases | `docs/phases/` | `phase-00.md` a `phase-14.md` | existentes |
| Requisitos | `docs/` | `requirements.yaml` | existente |
| Decisão do motor | `docs/adr/` | `ADR-0001-motor-de-agentes.md` | ACEITE |
| Decisão do gateway LLM | `docs/adr/` | `ADR-0002-gateway-de-modelos.md` | ACEITE |
| Contratos do gateway LLM | `app/llm/` | `contracts.py` | validados em `HCW-02-003` |
| Redacção e egress | `app/llm/egress/` | `policy.py`, `secret_scan.py`, `untrusted_wrap.py` | validados em `HCW-02-004`; redacção de corpo JSON reforçada em `HCW-02-014` |
| Consentimento cloud | `app/llm/` | `consent.py` | validado em `HCW-02-005` |
| Prompts versionados | `app/llm/prompts/` | `registry.py`, `system.md`, `revisao.md` | validados em `HCW-02-006` |
| Orçamento de modelo | `app/llm/budget/` | `tokens.py`, `tools_budget.py` | validado em `HCW-02-007` |
| Resiliência e escada do roteador | `app/llm/router/` | `errors.py`, `cooldown.py`, `ladder.py` | validada em `HCW-02-008` e `HCW-02-009` |
| Adaptadores sem SDK externo | `app/llm/providers/` | `common.py`, `gemini_text.py`, `ollama.py`, `gemini_live.py` | validados em `HCW-02-010`; instrumentação central em `HCW-03-007` |
| Observabilidade redigida das chamadas LLM | `app/llm/` | `observability.py` | implementada em `HCW-03-007` |
| Demonstração do gateway na CLI | `app/cli/` | `llm_ping.py`, `main.py` | implementada em `HCW-02-011` |
| Servidor local e API de tarefas/eventos/chamadas/chat/equipa/aprovação | `app/ui/server/` | `app.py`, `http_responses.py`, `routes_tasks.py`, `routes_events.py`, `routes_llm_calls.py`, `chat.py`, `routes_chat.py`, `routes_approvals.py`, `event_filters.py`, `auth.py`, `web_assets.py` | validado em `HCW-03-003` a `HCW-03-007`; chat persistido em `HCW-03-008`; recursos locais implementados em `HCW-03-009`; equipa e aprovação validadas em `HCW-04-010` |
| Cliente web local e desenho de ecrãs | `app/ui/web/` | `index.html`, `styles.css`, `agents.js`, `approvals.js`, `tasks.js`, `logs.js`, `llm_calls.js`, `chat.js` | implementado em `HCW-03-009`; filtros, chat e capturas reais validados em `HCW-03-010`; equipa e aprovação validadas em `HCW-04-010`; desenho em `DESIGN.md` na raiz |
| Auditoria inicial | `docs/reports/` | `audit.md` | VALIDADA em HCW-00-001 |
| Baseline de ambiente | `docs/reports/` | `baseline-freeze.txt` | VALIDADA em HCW-00-001 |
| Baseline de testes | `docs/reports/` | `baseline-tests.txt` | histórico: sem testes iniciais |
| Spike do motor | `docs/reports/` | `spike-agent-engine.md` | VALIDADO em HCW-00-009 |
| Evidências por tarefa | `docs/reports/` | `hcw-00-003.txt` a `hcw-00-008.txt` | existentes |
| Relatório `hcw llm ping` | `docs/reports/` | `hcw-02-011.md` | VALIDADO em HCW-02-011 |
| Relatório `ProviderError` | `docs/reports/` | `hcw-02-013.md` | IMPLEMENTADO em HCW-02-013; excepção normal e auditoria frozen |
| Relatório do adaptador Ollama | `docs/reports/` | `hcw-02-014.md` | VALIDADO em HCW-02-014; `/api/generate`, corpo restrito e `HCW_OLLAMA_MODEL`; teste real passou com timeout de 900 s |
| Saída do teste real Ollama | `docs/reports/` | `hcw-02-014-real.txt` | evidência: 653,46 s medidos pelo Utilizador e teste real passou em 896,82 s com `qwen3.5:4b` |
| Matriz de segurança da Fase 2 | `docs/reports/` | `phase-02-security.md` | validada em HCW-02-012; lacuna de endpoints em configuração; HCW-02-013 implementada e HCW-02-014 validada com teste real Ollama |
| Evidência real de interface da Fase 3 | `docs/reports/` | `phase-03-ui-evidence.md` | validada em HCW-03-010; capturas em `screenshots/phase-03/` |
| Matriz de segurança da Fase 3 | `docs/reports/` | `phase-03-security.md` | consolidada em HCW-03-011; token, `Origin`, `127.0.0.1` e prompt injection ligados a testes reais |
| Evidência real da equipa e aprovação da Fase 4 | `screenshots/phase-04/` | `01-equipa.png`, `02-aprovacao.png` | validada em HCW-04-010 com Chromium real sobre servidor local em porto efémero |
| Harness de avaliação da Fase 4 | `tests/eval/` | `cases.py`, `scorer.py`, `runner.py`, `test_reference_cases.py` | validado em HCW-04-011; cinco casos, pontuação mínima de 4 em 5 e caso dourado obrigatório |
| Gerador do relatório final | `reports/` | `final_report.py`, `tasks/HCW-04-011-avaliacao.json`, `tasks/HCW-04-011-metadados.json` | validado em HCW-04-011; `docs/reports/phase-04.md` sem segredos, token real ou prompt completo |
| Consolidação de segurança da Fase 4 | `docs/reports/` | `phase-04-security.md` | validada em HCW-04-012; ameaças ligadas a testes reais, executor não isolado documentado e relatórios sem segredos |
| Filtro determinístico de chamadas LLM | `app/ui/web/` | `llm_calls.js` | validado em HCW-04-013; respostas antigas de `/api/llm-calls` descartadas e teste real com um único item |
| Recusa segura de POST | `app/ui/server/` | `app.py` | validado em HCW-04-014; corpo drenado até `MAX_CORPO_BYTES` antes de fechar ligações recusadas |
| Mapa do código | `docs/` | `MAP.md` | este ficheiro |
| Plano de origem | `docs/` | `HybridCrewAI — Relatório Completo do Projecto e Plano Mestre v3.md` | referência histórica, não instrução |
| Skills do projecto | `.opencode/skills/` | `hcw-*/SKILL.md` | 10 Skills validadas pelo lint |
| CI | `.github/workflows/` | `ci.yml` | VALIDADA em HCW-00-008 |
| Hooks locais | raiz | `.pre-commit-config.yaml` | VALIDADOS em HCW-00-007 |
| Persona do assistente | raiz | `persona.md` | criada em HCW-04-002; sem segredos e sem execução automática |
| Definições dos agentes | `agents/definitions/` | `parser.py` | cinco definições validadas em HCW-04-003; conteúdo não confiável delimitado |
| Runner dos agentes | `agents/runner/` | `engine.py` | validado em HCW-04-004; `ToolResult` verificado, três tentativas no máximo e `approved` do modelo sem efeito |
| Tokens de aprovação | `approvals/tokens/` | `models.py`, `store.py` | validados em HCW-04-005 e expostos na UI em HCW-04-010; emissão só pela UI autenticada, ligação a tarefa/correlação/diff e expiração de 15 minutos |
| Fluxo CREATE com checkpoints | `workflows/create/` | `orchestrator.py`, `state.py` | validado em HCW-04-006 e HCW-04-009; oito passos, token da UI obrigatório, idempotência confirmada após sucesso e recuperação após cancelamento ou morte do processo |
| Executor simples com aprovação | `execution/` | `simple_runner.py`, `guard.py`, `models.py` | implementado em HCW-04-007; `isolated=false`, subprocesso com token, pasta temporária, ambiente limpo, guarda Python e prazo/cancelamento |
| Configuração de ferramentas | raiz | `pyproject.toml` | validada em HCW-00-004 |
| Dependências fixadas | raiz | `requirements.lock.txt` | 27 pacotes, incluindo Playwright fixado em HCW-03-010 |
| Ambiente virtual | `.venv/` | `pyvenv.cfg` | ignorado pelo Git |
| Configuração do editor | `.vscode/` | `settings.json` | aponta para o `.venv` |

## Ficheiro legado fora do Git

`STATE .md` (com espaço antes da extensão) é uma cópia antiga e não deve ser usada. A fonte activa é `STATE.md`, sem espaço. A renomeação/remoção do ficheiro legado exige decisão do utilizador.

## Estrutura prevista — em construção

A árvore abaixo é a meta do plano; as pastas só devem ser criadas quando a fase correspondente as exigir. A Fase 1 criou `app/core/` e `app/cli/`; a Fase 2 criou os módulos de `app/llm/` e ligou a CLI ao gateway; a Fase 3 criou `app/ui/` com servidor local, autenticação, API de tarefas e stream SSE de eventos.

| Responsabilidade futura | Pasta prevista | Fase |
|---|---|---|
| Configuração, eventos, tarefas, logs e resultados | `app/core/` | 1 (concluída) |
| Fornecedores LLM, encaminhamento, egress e orçamento | `app/llm/` | 2 (gateway com adaptadores e demonstração na CLI) |
| Servidor e interface web | `app/ui/`, `app/ui/web/` | 3 (servidor e cliente local validados; evidência real em `HCW-03-010`) |
| Fluxo CREATE ponta a ponta | `workflows/create/` | 4 (núcleo validado em HCW-04-006; caso dourado validado em HCW-04-008; cancelamento e retoma validados em HCW-04-009) |
| Workspace, ZIP, snapshots e auditoria | `app/workspace/` | 5 (caminhos, scan, anexos, ZIP e snapshots/rollback validados) |
| Execução isolada | `app/execution/` | 6 |
| Análise de código e grafo | `app/analysis/` | 7 |
| Conhecimento | `app/knowledge/` | 10 |
| Voz e Gemini Live | `app/voice/` | 11 |
| Ferramentas de computador, rede e engenharia reversa | `app/tools/` | 12 e 13 |
| Autonomia, rotinas e checkpoints | `app/autonomy/` | 9 |
| Aprovações por token e diff | `approvals/tokens/` | 4 e 12 (tokens validados em HCW-04-005) |
| CLI de utilizador | `app/cli/` | 1 (logs/doctor, concluída), 2 (`llm ping`) e 14 |
| Dados locais e relatórios gerados | `config/`, `data/`, `projects/`, `reports/`, `logs/` | conforme necessário |
| Testes por natureza | `tests/unit/`, `integration/`, `contracts/`, `security/`, `recovery/`, `ui/`, `eval/`, `fixtures/` | fases seguintes |

## Fecho da auditoria da Fase 0

- Entregas verificadas: baseline, 18 testes de guardas, CI em dois sistemas, pre-commit, Git com tag inicial, spike documental e ADR-0001.
- Ameaça tratada: `Dependência ou ferramenta comprometida` — versões fixadas e CI com acções oficiais; evidência em `docs/reports/hcw-00-008.txt`.
- Ameaça tratada: `Acção reportada como feita sem o ter sido` — evidências por saída real e códigos de saída nos relatórios de tarefa.
- Limitação aberta: `HCW-00-006` permanece `IMPLEMENTED`; `ruff` e `mypy` têm erros pré-existentes fora do âmbito desta tarefa.
- Limitação da Fase 0: na altura da auditoria não existia aplicação, servidor nem funcionalidade de utilizador; o núcleo foi criado na Fase 1.
- Segredo: nenhuma credencial foi encontrada nos inventários de auditoria; nenhuma foi acrescentada nesta tarefa.

## Fecho da Fase 1

- Entregas verificadas: configuração, segredos, eventos, logging, máquina de estados, SQLite, `ToolResult` e CLI; 90 testes passam e o gate deu `GO`.
- Ameaças tratadas: `Perda de trabalho em falhas` com teste real de `kill()`, `Fuga de segredos para logs/cloud` com redacção verificada e `Acção reportada como feita sem o ter sido` com `ToolResult`.
- Evidência: `reports/phase-01/report.md`, `reports/phase-01/report.json` e `docs/reports/phase-01.md`.
- Etiqueta local `phase-01-go` criada no commit `696ccdb600195fcec5f0a56a91449989a9167528`.
- Limitação aberta: ainda não há servidor, interface web, cloud, workspace nem execução isolada; essas superfícies começam nas Fases 2 a 6.
- Limitação aberta: `ruff check .` e `mypy scripts` continuam a apontar erros pré-existentes em `scripts/` (`HCW-00-006`).

## Consolidação de segurança da Fase 2

- Matriz em `docs/reports/phase-02-security.md`: fallback, timeout, egress com servidor falso, consentimento, prompt injection e orçamento de ferramentas têm testes executados.
- `THREAT_MODEL.md` liga egress, prompt injection e falha de fornecedor aos testes concretos; custos e quotas apontam para `tests/unit/test_llm_budget.py` e `tests/unit/test_llm_contracts.py`.
- Lacuna aberta: endereços de fornecedores não são carregados por `Settings`/`load_settings()`; `HCW-02-014` implementou apenas `HCW_OLLAMA_MODEL`, `POST /api/generate` e corpo restrito. Endereços Gemini continuam sem configuração.
- Correcção implementada: `HCW-02-013` corrige `ProviderError` como excepção normal, prova a propagação via `@contextmanager` e vigia outras excepções frozen; relatório em `docs/reports/hcw-02-013.md`.
- Correcção implementada: `HCW-02-014` usa `POST /api/generate`, rejeita NDJSON/`done:false`, retira metadados internos do corpo e protege a serialização JSON no egress; relatório em `docs/reports/hcw-02-014.md` e saída real em `docs/reports/hcw-02-014-real.txt`.
- Gate da Fase 2 **GO** em 2026-11-23T16:58:59 (`reports/phase-02/report.md`); `HCW-02-999` permanece `NOT_STARTED`. Fase 2 commitada e enviada para `origin/master`; etiqueta `phase-02-go` reposicionada para o commit final.
- Teste real de `tests/integration/test_llm_real.py` com `qwen3.5:4b` passou com timeout de 900 s em 896,82 s; o modelo tem `thinking default true` e o contrato aprovado não permite enviar `think: false`. Gemini continua skipped por falta de endpoint/credencial.

## Consolidação de segurança da Fase 3

- Matriz em `docs/reports/phase-03-security.md`: token em memória, `Origin`, `127.0.0.1`, CSP, whitelist local e prompt injection têm testes executados.
- `THREAT_MODEL.md` liga token, `Origin`, loopback e prompt injection a testes concretos, incluindo `tests/ui/test_browser.py::test_evidencia_real_no_browser`.
- Evidência real de browser em `docs/reports/phase-03-ui-evidence.md`, com capturas em `screenshots/phase-03/` e SHA-256 registado.
- Dependências fixadas passaram a 27 pacotes com `playwright==1.65.2` e `greenlet==3.5.6`, após aprovação explícita do Utilizador.
- Limitação aberta: o token ainda tem de ser reintroduzido após recarregar a página; a falha por Chromium ausente não foi simulada depois da instalação.

## Consolidação da Fase 4

- Harness em `tests/eval/`: cinco casos de referência, `digest_casos` canónico e `ResultadoAvaliacao.aprovado` dependente do caso dourado e da pontuação mínima de 4 em 5.
- Relatório final em `docs/reports/phase-04.md`: 126 linhas, comandos, resultados, critérios de aceitação, evidências, limitações e digests; gerado por `reports/final_report.py` com `--metadados`.
- Evidência em `reports/tasks/HCW-04-011.md` e `reports/tasks/HCW-04-011-tests.txt`; 10 testes próprios, 44 na regressão focada e 307 na regressão integral com uma falha pré-existente deseleccionada.
- Limitação aberta: o executor do caso dourado não é isolado; a guarda reduz ficheiros e rede, mas não é uma sandbox.

## Como usar este mapa

1. Para estado do plano, abrir `STATE.md` e correr `python scripts/plan_status.py`.
2. Para decisões de arquitectura, abrir `docs/adr/ADR-0001-motor-de-agentes.md` e `docs/adr/ADR-0002-gateway-de-modelos.md`.
3. Para evidência de CI, abrir `docs/reports/hcw-00-008.txt`.
4. Para o ponto de partida, abrir `docs/reports/audit.md`.
