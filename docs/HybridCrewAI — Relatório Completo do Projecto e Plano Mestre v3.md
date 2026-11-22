# HybridCrewAI — Relatório Completo do Projecto e Plano Mestre v3

*Assistente pessoal estilo JARVIS com equipa de agentes autónomos de engenharia de software · Versão 3.0.0 · 21 de Novembro de 2026 · Estado: proposta para aprovação · Português de Portugal*

Este documento consolida e substitui o Plano Mestre v2 e os ajustes posteriores (Gemini Live como principal, ecrã de Chat com anexos, Stitch, REA, lições do Mark LVII). Está organizado em três blocos: **decisões e arquitectura** (secções 1 a 10), **fases de implementação** (secções 11 a 12) e **Skills, mecanismos de controlo e anexos** (secções 13 a 20).

## 1. Sumário executivo

**O que é.** Um assistente pessoal, com voz e texto, a que se dão instruções em linguagem natural e que coordena agentes que trabalham sozinhos para criar, analisar, melhorar e manter projectos de software, com progresso visível, controlo humano nos pontos críticos e recuperação de falhas.

**Como se constrói.** Em 15 fases (0 a 14), cada uma entregando algo que se vê e se usa. Cada fase termina num *gate* executável (`hcw accept --phase N`) que corre testes reais e dá GO ou NO-GO. A fase seguinte só começa com GO.

**Decisões que definem o projecto:**

1. **Gemini Live é sempre o provedor principal** da conversa e da voz; modelos de texto Gemini fazem o trabalho dos agentes de engenharia; o **Ollama fica em segundo plano** (tarefas leves e modo degradado), porque o hardware local não tem capacidade para o papel principal.
2. **Núcleo próprio e fino** (máquina de estados, event bus, saída estruturada), com o CrewAI e outros frameworks como adaptadores substituíveis. A escolha final é feita por evidência, num *spike* na Fase 0.
3. **Interface web local** (FastAPI + SSE/WebSocket + frontend leve), disponível desde a Fase 3 como «janela de vidro» sobre o núcleo.
4. **Ficheiros pequenos impostos por script** (máximo 300 linhas), um README.txt e um `module.yaml` por módulo.
5. **Segurança antes de poder:** workspace seguro, snapshots e execução isolada precedem qualquer capacidade de escrita ou execução alargada.
6. **Ideias do Mark LVII adoptadas** onde reforçam o plano: resultados verificados, confirmação não forjável, agentes como ficheiros Markdown, tarefas em segundo plano com orçamento, rotinas, escada de modelos.

**O que mudou em relação ao plano v2:** passa a existir a Fase 12 (controlo do computador), a Fase 13 (engenharia reversa via REA, opcional) e a Fase 14 (avaliação contínua, documentação e distribuição); o ecrã de Chat com anexos fica explícito; a política cloud muda de «consentimento por chamada» para «autorização única + egress sempre activo»; entram os mecanismos de continuidade (`STATE.md`, `DEVLOG.md`, `IDEAS.md`).

## 2. Visão e âmbito

### 2.1 Modos de trabalho

| Modo | Responsabilidade |
| --- | --- |
| **CREATE** | Criar aplicações de raiz a partir de um pedido |
| **ANALYZE** | Inspeccionar e avaliar projectos existentes (pastas, ZIP) |
| **IMPROVE** | Corrigir, refactorizar e evoluir projectos existentes |
| **MAINTAIN** | Actualizar, testar e acompanhar projectos ao longo do tempo |

Os quatro modos partilham a mesma infraestrutura de engenharia.

### 2.2 O que o sistema faz

Interpreta pedidos; produz requisitos, planos e arquitecturas; gera código e testes; executa-os em isolamento; analisa resultados e corrige; documenta; mantém histórico e memória; comunica progresso por voz e texto; aceita interrupções; trabalha em tarefas longas sem perder estado.

### 2.3 O que o sistema não é

- Não é um simples gerador de código: mantém visão global, rastreabilidade e validação.
- Não executa comandos nem código vindos de um modelo sem passar por serviços determinísticos e permissões.
- Não depende de um único framework de agentes nem de um único fornecedor de modelos.
- Não clona nem copia software de terceiros; a engenharia reversa (Fase 13) tem âmbito legal limitado.

### 2.4 Âmbito de linguagens

**Python-first** para geração e testes. Outras linguagens só em modo de análise, até haver decisão em contrário.

## 3. Decisões e pendências

| ID | Decisão | Estado |
| --- | --- | --- |
| D-01 | Gemini Live como provedor principal de conversa e voz | **Fechada** |
| D-02 | Modelos de texto Gemini (escada com *cooldown*) para os agentes de engenharia | **Fechada** |
| D-03 | Ollama em segundo plano: tarefas leves e modo degradado | **Fechada** |
| D-04 | Consentimento cloud único no primeiro arranque; scan de segredos e exclusões sempre activos | Proposta |
| D-05 | Núcleo próprio + adaptadores (CrewAI, LangGraph); decisão final pelo *spike* da Fase 0 | Proposta |
| D-06 | Interface: FastAPI + SSE/WebSocket + frontend leve, apenas em 127.0.0.1 | Proposta |
| D-07 | Stitch usado só para desenhar ecrãs; o produto não depende dele | Proposta |
| D-08 | Python-first | Proposta |
| D-09 | Máximo de 300 linhas por ficheiro, imposto por script | Proposta |
| D-10 | Autonomia L1 por defeito, a subir por fases com testes | Proposta |
| D-11 | Identificadores e nomes de ficheiros em inglês; documentação, comentários e interface em PT-PT | Proposta |
| D-12 | REA como extensão opcional (Fase 13) | Proposta, aguarda finalidade |
| D-13 | Controlo do computador numa fase própria (Fase 12) | Proposta |

**Pendências (não bloqueiam o arranque):**

- **P-01 ByteByteGo:** é conteúdo educativo de *system design*, não uma ferramenta; fica como referência de leitura, sem integração.
- **P-02 Ferramentas de redes:** por clarificar (utilitários de diagnóstico?). Se forem, entram como ferramentas só de leitura com lista de destinos permitidos.
- **P-03 Finalidade do REA:** software próprio, terceiros ou malware? Decide avisos legais e permissões.
- **P-04 Hardware:** RAM e GPU da máquina, para dimensionar o Ollama e a voz offline.
- **P-05 Conta Gemini:** com facturação activa (recomendado) ou quota gratuita.

## 4. Análise do Mark LVII e ideias adoptadas

O Mark LVII (repositório `FatihMakes/Mark-LVII`) é um assistente em tempo real que ouve, vê, fala e controla o computador, sobre a Gemini Live API, com motor local opcional. **Não é uma equipa de engenharia de software**: o nosso projecto é a camada JARVIS mais uma fábrica de software. A análise baseou-se no README, não no código; as medições citadas são afirmações do autor. Adoptamos ideias, não código.

| Ideia do Mark LVII | Onde entra no nosso plano |
| --- | --- |
| Resultados verificados: `done`, `unverified`, `failed`, `ask`, `started` | Contrato `ToolResult` (Fase 1) |
| Confirmação emitida pela interface, não pelo modelo | Aprovações (Fases 4 e 5) |
| Agentes como ficheiros Markdown com ferramentas e orçamento | Agentes (Fase 4) |
| Tarefas em segundo plano com orçamento, checkpoint por passo e pausa por quota | Fase 9 |
| Citações verificadas em código contra a página guardada | Planeador e ADR (Fases 4 e 7) |
| Motor único de rotinas e horas de silêncio | Fase 9 |
| Escada de modelos com *cooldown* por tipo de erro e timeout em todas as chamadas | LLM Gateway (Fase 2) |
| Orçamento de ferramentas e descrições curtas para modelos pequenos | Gateway/Ollama (Fase 2) |
| Honestidade de plataforma (Wayland, permissões do macOS) | Fases 11 e 12 |
| Push-to-talk, guarda contra eco, teste de microfone, dispositivos de áudio | Voz (Fase 11) |
| Memória recuperável com índice de chaves; Undo | Fases 10 e 5 |
| Plugins de um só ficheiro com auto-descoberta | Ferramentas (Fase 12) |
| Importações preguiçosas (o que não se usa não custa) | Regra transversal |
| Conteúdo externo marcado como dados | Defesa contra *prompt injection* (Fase 2) |

**Lições de segurança que o próprio README documenta** (injecção de comandos num `open_app`, ferramenta que executava Python escrito pelo modelo, fecho da janela errada) confirmam as nossas regras: o modelo propõe e o Python executa, com permissões e verificação.

## 5. Arquitectura

### 5.1 Camadas

```text
Interface (voz, texto, web)          ← só consome eventos e envia comandos
        │
Concierge (JARVIS)                   ← traduz conversa em tarefas; persona
        │
Orquestrador (determinístico)        ← estados, filas, aprovações, checkpoints
   │         │          │          │
Agentes   Workspace   Execução   Qualidade   ← serviços sem LLM, com permissões
   │
LLM Gateway                          ← Gemini Live · Gemini texto · Ollama
        │
Núcleo: configuração · event bus · SQLite · logging JSONL · ToolResult
```

### 5.2 Provedores por papel

| Papel | Provedor |
| --- | --- |
| Conversa e voz em tempo real | **Gemini Live** |
| Agentes de engenharia | Modelos de texto Gemini, com escada e *cooldown* |
| Segunda linha cloud | Outros provedores, extensão futura (exige autorização própria) |
| Segundo plano e modo degradado | **Ollama** (resumos, classificação, logs, rotinas) |

### 5.3 Equipa de agentes

| Agente | Função |
| --- | --- |
| **Concierge (JARVIS)** | Conversa, traduz pedidos em tarefas, comunica progresso; não escreve código |
| **Planeador** | Requisitos, riscos, plano técnico |
| **Arquitecto** | Arquitectura e contratos (inclui o papel de Designer no início) |
| **Construtor** | Gera código por ficheiro dentro dos contratos |
| **Testador** | Cria e analisa testes e resultados |
| **Revisor** | Critica as saídas dos outros antes de chegarem ao utilizador |

O **Orquestrador não é um agente LLM**: é código determinístico que decide a ordem, aplica permissões, executa operações e grava estado. Os agentes só propõem.

### 5.4 Níveis de autonomia

- **L0 — Sugerir:** nada é aplicado.
- **L1 — Aprovar tudo:** cada alteração precisa de aprovação (por defeito).
- **L2 — Aprovar nos gates:** trabalha sozinho entre pontos de controlo.
- **L3 — Autónomo com orçamento:** limites de tempo, tokens, iterações e pasta; botão de paragem sempre visível.

A autonomia só sobe quando os testes de segurança do nível anterior passam.

### 5.5 Política cloud e fallbacks

- **Autorização cloud única** no primeiro arranque, mais o interruptor por projecto «pode enviar código para a cloud».
- **Egress sempre activo:** scan de segredos, redacção e exclusão de ficheiros sensíveis antes de qualquer envio.
- **Entre modelos Gemini:** fallback automático.
- **Para outro provedor cloud:** exige autorização desse provedor.
- **Para o Ollama:** permitido (nada sai da máquina), mas só para tarefas leves; uma tarefa de código fica em pausa e pede decisão.
- **Dados e termos:** nos serviços gratuitos a Google pode usar o conteúdo para melhorar produtos e revisores humanos podem lê-lo; nos pagos não. Recomenda-se activar a facturação antes de enviar código real e confirmar sempre os termos em vigor.

## 6. Contratos transversais

### 6.1 ToolResult (resultados verificados)

Toda a ferramenta devolve `status` (`done` · `unverified` · `failed` · `ask` · `started`), `message`, `evidence` e `data`. Regras: `done` só com verificação real (nunca assumido de um código de retorno); `unverified` nunca é comunicado como sucesso; `ask` significa que nada foi feito porque agir seria adivinhar; `started` indica que o resultado chega depois, por evento.

### 6.2 Aprovações não forjáveis

Uma aprovação é um *token* de utilização única, emitido **apenas pela interface**, ligado ao *hash* do diff e com validade curta. Nenhum parâmetro preenchido por um modelo pode aprovar uma acção.

### 6.3 Agentes como ficheiros Markdown

```markdown
---
name: builder
role: Construtor
tools: [workspace.read, workspace.propose_change]
model_tier: text-pro
budget: {minutes: 10, steps: 40, tokens: 120000}
autonomy_max: L2
---
Instruções do agente em PT-PT. Respeita os contratos; reutiliza antes de criar.
```

Adicionar um agente é criar um ficheiro. O cabeçalho é validado por esquema; as ferramentas listadas são o máximo que o agente pode pedir.

### 6.4 Eventos

Cada evento é uma linha JSON: `ts`, `level`, `correlation_id`, `task_id`, `agent`, `phase`, `event`, `data`. Eventos previstos: `task.created`, `task.started`, `task.progress`, `task.waiting_approval`, `task.paused`, `task.resumed`, `task.completed`, `task.failed`, `task.cancelled`, `agent.started`, `agent.completed`, `workflow.stage_changed`, `workspace.changed`, `test.completed`, `llm.call`.

### 6.5 Estados de uma tarefa

`CREATED → QUEUED → RUNNING → WAITING_APPROVAL ⇄ PAUSED → COMPLETED`, com os ramos `FAILED`, `CANCELLING → CANCELLED` e `RECOVERING`. As transições inválidas são rejeitadas por código e testadas.

### 6.6 Persona

Um ficheiro versionado (`persona.md`) define nome, tom e tratamento do assistente, e é carregado pelo Concierge. Alterável por voz ou pela interface.

## 7. Regras de manutenção

| Regra | Limite | Verificação |
| --- | --- | --- |
| Linhas por ficheiro | Aviso aos 200, falha aos 300 | `scripts/check_file_size.py` (CI e pre-commit) |
| Linhas por função | 40 | Ruff |
| Responsabilidade | Um ficheiro, uma responsabilidade | Revisão + Revisor |
| Pasta de módulo | `README.txt` + `module.yaml` | `scripts/check_modules.py` |
| Importações | Só pela API pública (`__init__.py`) | Teste de dependências |
| Erros | Excepções tipadas com causa e acção sugerida | Testes de contrato |
| Rastreio | Todo o evento leva `correlation_id`, `task_id`, `agent`, `phase` | Teste de logging |
| Importações pesadas | Preguiçosas (carregadas no primeiro uso) | Teste de tempo de arranque |
| Diagnóstico | `hcw doctor` | Corre em cada gate |
| Mapa do código | `docs/MAP.md` gerado: «onde está o quê» | CI |

Para encontrar um problema: abrir a consola de logs, filtrar pelo `correlation_id`, ver o evento falhado e o módulo que o emitiu; o `MAP.md` indica a pasta.

### Estrutura de pastas proposta

```text
HybridCrewAI/
├── app/
│   ├── core/        config/ events/ tasks/ logging/ results/
│   ├── llm/         providers/ router/ egress/ prompts/ budget/
│   ├── agents/      definitions/ (*.md)  runner/  adapters/
│   ├── workflows/   create/ analyze/ improve/ maintain/
│   ├── workspace/   paths/ scanner/ archive/ snapshot/ audit/
│   ├── execution/   executors/ limits/ capture/
│   ├── analysis/    scanners/ graph/ quality/
│   ├── knowledge/   store/ search/
│   ├── voice/       live/ stt/ tts/ session/
│   ├── tools/       registry/ computer/ network/ reverse/
│   ├── autonomy/    budgets/ routines/ checkpoints/
│   ├── approvals/   diff/ tokens/
│   ├── ui/          server/ web/
│   └── cli/         logs doctor accept
├── config/  data/  projects/  reports/  logs/
├── docs/            architecture/ adr/ modules/ MAP.md
├── skills/          (Skills do projecto)
├── tests/           unit/ integration/ contracts/ security/ recovery/ ui/ eval/ fixtures/
├── scripts/
├── tasks.yaml  STATE.md  DEVLOG.md  IDEAS.md  THREAT_MODEL.md
└── pyproject.toml  README.md  README.txt
```

A árvore é uma meta; só se criam as pastas quando a fase respectiva as exige.

## 8. Interface gráfica

### 8.1 Tecnologia

**FastAPI + SSE/WebSocket + frontend leve (HTML, CSS e JavaScript em módulos pequenos), apenas em `127.0.0.1`.** O Flask serviria, mas é síncrono por natureza; para logs em tempo real, voz e tarefas paralelas o FastAPI encaixa melhor e partilha esquemas Pydantic com o núcleo. A interface é um consumidor do event bus: trocar de tecnologia no futuro não toca no núcleo.

### 8.2 Ecrãs por fase

| Ecrã | Conteúdo | Fase |
| --- | --- | --- |
| **Chat** | Texto (e voz), anexos de ficheiros, pastas e ZIP, relatório de cobertura | 3 (texto), 5 (ZIP completo), 11 (voz) |
| **Consola de logs** | Tempo real, filtros por tarefa/agente/nível/correlation ID | 3 |
| **Tarefas** | Estado, progresso, pausar/retomar/cancelar | 3 |
| **Chamadas LLM** | Fornecedor, modelo, latência, tokens, tentativas, fallback | 3 |
| **Equipa de agentes** | Quem trabalha, em quê, com que autonomia | 4 |
| **Aprovações e diff** | Por ficheiro e por bloco, ligado ao snapshot | 5 |
| **Snapshots** | Linha temporal com rollback | 5 |
| **Permissões** | Workspaces, cloud por projecto | 5 |
| **Testes e execução** | Resultados, cobertura, stdout/stderr | 6 |
| **Análise de código** | Árvore, grafo de dependências, Ruff/mypy/Bandit | 7 |
| **Git e alterações** | Ramos e commits por tarefa | 8 |
| **Custos, quotas, rotinas** | Tokens por agente, limites, rotinas e horas de silêncio | 9 |
| **Memória** | Decisões e conhecimento por projecto | 10 |
| **Voz** | Escuta, transcrição, interrupção | 11 |
| **Centro de comando** | Ecrã principal estilo HUD com tudo num olhar | 9 em diante |

### 8.3 Chat com ficheiros, pastas e ZIP

- **Duas formas de adicionar conteúdo:** arrastar ficheiros, pastas ou ZIP para o chat, ou indicar o caminho de uma pasta do disco, que passa a ser um workspace autorizado.
- **Os anexos vão primeiro para uma área de entrada (quarentena)**, nunca directamente para o workspace; só depois de analisados e aprovados passam a ser usados.
- **Leitura recursiva completa**, incluindo subpastas e ZIP dentro de ZIP (limite de profundidade e de tamanho total).
- **Relatório de cobertura visível**, para que nada seja ignorado em silêncio, por exemplo: «312 ficheiros encontrados, 290 lidos, 14 binários ignorados, 6 acima do limite, 2 sensíveis (não seguem para a cloud)». O número tem de bater com o disco.

### 8.4 Stitch (apenas desenho)

O Stitch (Google Labs) gera maquetes de interface a partir de texto e exporta HTML com Tailwind, ZIP, MCP ou Figma. Uso previsto: desenhar na Fase 3 os ecrãs base, exportar, dividir em ficheiros pequenos e ligar ao event bus; guardar o `DESIGN.md` no repositório para manter o estilo. Cuidados: é um serviço cloud (não colar código ou dados de projectos reais); o código exportado é um andaime (acessibilidade e valores fixos a rever); o CSS compila-se localmente para a aplicação funcionar offline em 127.0.0.1.

### 8.5 Segurança local

Só escuta em `127.0.0.1`; *token* de sessão; verificação de *Origin* contra ataques via browser; sem CORS aberto; comandos destrutivos pedem confirmação por token emitido pela interface. O acesso a partir do telemóvel, se vier a existir, é uma extensão posterior com emparelhamento, limites de tentativas e expiração de sessões.

## 9. Estratégia de testes e gates

- **Real por defeito:** SQLite real, sistema de ficheiros real (pastas temporárias), processos reais (incluindo matar o processo a meio), servidor web real com browser automatizado (Playwright).
- **Mocks só onde não há alternativa:** falhas de fornecedores (timeout, 429, resposta inválida) e testes que não podem custar dinheiro.
- **Marcadores:** `live_local` (Ollama), `live_cloud` (Gemini, opcional e autorizado), `ui`, `security`, `recovery`, `eval`.
- **Comando único:** `hcw accept --phase N` corre os testes da fase **e** de todas as anteriores (regressão acumulada) e escreve `reports/phase-N/report.html` e `.json` com GO/NO-GO, capturas de ecrã e logs como evidência.
- **Regra de ouro:** a fase N+1 só começa com GO na fase N; uma tarefa só passa a VALIDATED com evidência anexada.
- **Harness de avaliação:** pedidos de referência com resultado esperado e pontuação, para detectar regressões ao mudar de prompt ou de modelo (5 casos na Fase 4, 20 ou mais na Fase 14).
- **Etiquetas Git:** cada fase fechada recebe uma etiqueta (`phase-03-go`) para se poder voltar atrás.

## 10. Matriz de activação por fase

Cada capacidade fica atrás de uma *feature flag* na configuração, **desligada até a fase que a valida dar GO**.

| Fase | Passa a ligar-se | Autonomia máxima | Permissões novas |
| --- | --- | --- | --- |
| 0 | Guardas de CI, validação do plano | — | Nenhuma |
| 1 | `core` (config, eventos, tarefas, logs, `ToolResult`) | L0 | Leitura da configuração |
| 2 | `gateway` (Live, texto, Ollama; egress) | L0 | Rede para provedores autorizados |
| 3 | `ui` (logs, tarefas, chamadas LLM) | L0 | Servidor local 127.0.0.1 |
| 4 | `create_flow`, Chat de texto, agentes Markdown, aprovações na UI | L1 | Escrita em pasta temporária; executor mínimo com aprovação |
| 5 | `workspace_write`, snapshots, diff, ZIP, Permissões | L1 | Escrita em workspaces autorizados |
| 6 | `sandbox_exec` | L1 | Execução isolada de código |
| 7 | `analysis` (scanners, painel de análise) | L1 | Leitura recursiva |
| 8 | `improve_git` | L2 | Operações Git no workspace |
| 9 | `background_tasks`, rotinas, horas de silêncio, orçamentos | L2 (L3 só com testes) | Execução agendada |
| 10 | `memory` | L2 | Armazenamento de conhecimento |
| 11 | `voice` (Gemini Live, offline opcional) | L2 | Microfone e altifalantes |
| 12 | `computer_control` (ferramentas com `ToolResult`) | L1 nesta área | Controlo do computador, sempre com confirmação |
| 13 | `reverse_eng` (REA via MCP) | L1 | Análise de binários só no sandbox; instalação com aprovação |
| 14 | Avaliação contínua, documentação automática, distribuição | L2/L3 | Instalador |

## 11. Fichas de fase (0 a 7)

Cada ficha tem a mesma estrutura: objectivo, o que activa, ficheiros principais (todos pequenos), testes reais, demonstração, *gate* e recuperação.

### Fase 0 — Fundação, auditoria e escolha do motor

**Objectivo:** conhecer o estado real do código existente, montar a linha de montagem de qualidade e decidir o motor de agentes com evidência.

**Activa:** guardas de CI e validação do plano.

**Ficheiros:** `pyproject.toml`; CI (GitHub Actions, Windows e Linux); pre-commit; `scripts/check_file_size.py`, `check_modules.py`, `validate_plan.py`, `check_traceability.py`, `lint_skills.py`; `tasks.yaml`; `STATE.md`, `DEVLOG.md`, `IDEAS.md`, `THREAT_MODEL.md`; relatório de auditoria; spike do motor; `ADR-0001`; Git com etiquetas por fase.

**Testes reais:**

- executar a suite existente (referência histórica: 197 testes) e guardar a baseline: quantos passam, falham ou estão desactivados;
- o `check_file_size.py` tem teste próprio: um ficheiro de 301 linhas tem de falhar;
- instalação limpa num ambiente virtual novo, em Windows e Linux;
- spike: o mesmo cenário (pedido → plano estruturado → pausa → matar o processo → retoma) em núcleo próprio, CrewAI e LangGraph, com tabela de linhas de código, dependências, tempo de arranque e facilidade de retoma;
- `lint_skills.py` valida o *frontmatter* e o tamanho das Skills.

**Demonstração:** relatório de auditoria e tabela do spike, abertos no browser.

**Gate:** baseline guardada; CI verde nos dois sistemas; ADR-0001 aprovado.

**Recuperação:** etiqueta `phase-00-go`; a auditoria não altera código.

### Fase 1 — Núcleo: configuração, eventos, tarefas, persistência

**Objectivo:** a espinha dorsal que tudo o resto usa.

**Activa:** `core`.

**Ficheiros (exemplo):**

```text
app/core/config/    schema.py  loader.py  defaults.py  secrets.py
app/core/events/    models.py  bus.py  jsonl_sink.py
app/core/tasks/     model.py  state_machine.py  store_sqlite.py  ids.py
app/core/logging/   setup.py  correlation.py  redaction.py
app/core/results/   tool_result.py  statuses.py
app/cli/            logs.py  doctor.py
```

**Testes reais:**

- criar, correr e concluir uma tarefa com SQLite real;
- **matar o processo a meio** e verificar que o estado recupera;
- transições inválidas rejeitadas (ex.: COMPLETED → RUNNING);
- chave de API falsa nunca aparece nos logs;
- configuração inválida dá erro claro, sem arrancar;
- `ToolResult`: um `done` sem evidência é rejeitado pelo esquema;
- `hcw logs --follow` mostra em tempo real os eventos de uma tarefa real.

**Demonstração:** correr uma tarefa de teste, matar o processo, relançá-lo e ver a tarefa retomar.

**Gate:** recuperação após *kill* comprovada; zero segredos nos logs; `hcw doctor` verde.

**Recuperação:** migrações de configuração reversíveis; base de dados com cópia antes de cada migração.

### Fase 2 — LLM Gateway com política de egress

**Objectivo:** uma única porta para os modelos, com controlo do que sai para a cloud.

**Activa:** `gateway`.

**Ficheiros:** `llm/contracts.py`; `providers/gemini_live.py`, `gemini_text.py`, `ollama.py`; `router/ladder.py`, `cooldown.py`, `errors.py`; `budget/tokens.py`, `tools_budget.py`; `egress/secret_scan.py`, `policy.py`, `untrusted_wrap.py`; `prompts/registry.py` e `prompts/*.md` versionados.

**Decisões a confirmar em ADR:** reutilizar o LiteLLM para o Gemini de texto (reutilizar antes de criar); o Gemini Live pode exigir o SDK nativo da Google, caso em que o `LiveSession` fica atrás de um contrato próprio, para que o resto do sistema não dependa do SDK.

**Testes reais:**

- Ollama real (`live_local`): resposta estruturada válida;
- Gemini real (`live_cloud`, opcional): texto e uma sessão Live curta;
- falhas simuladas (timeout, 429, resposta inválida): classificação correcta, *retries* limitados, *cooldown* diferente por tipo de erro;
- **teste de timeouts:** falha se existir alguma chamada a um modelo sem prazo definido;
- **matriz de fallback:** Gemini→Gemini automático; Gemini→outro cloud só com autorização; Gemini→Ollama só para tarefas leves, com pausa e pedido de decisão nas tarefas de código;
- **egress:** servidor HTTP local falso capta o pedido; um ficheiro com chave falsa (`AKIA…`) não pode aparecer no payload;
- primeiro arranque: pede o consentimento cloud único e o tipo de conta;
- *prompt injection*: ficheiro com «ignora as instruções anteriores» segue como bloco de dados delimitado; o marcador de fecho não pode ser forjado;
- orçamento de ferramentas: o Ollama recebe a lista curta com descrições breves.

**Demonstração:** `hcw llm ping` mostra o fornecedor escolhido, latência e o que seria enviado, já redigido.

**Gate:** matriz de fallback completa; zero segredos no payload; quotas e orçamento a funcionar.

**Recuperação:** a escada de modelos é configuração, não código; um modelo retirado muda-se num ficheiro.

### Fase 3 — Interface web mínima e Chat de texto

**Objectivo:** ver o sistema a trabalhar desde cedo.

**Activa:** `ui`.

**Ficheiros:** `ui/server/app.py`, `routes_tasks.py`, `routes_events.py` (SSE/WebSocket), `routes_chat.py`, `auth.py`; `ui/web/index.html`, `logs.js`, `tasks.js`, `llm_calls.js`, `chat.js`, `styles.css`; `DESIGN.md`.

**Ecrãs:** consola de logs, tarefas, chamadas LLM, saúde e Chat de texto (sem anexos ainda). Os ecrãs base são desenhados no Stitch e exportados como andaime.

**Testes reais (Playwright):**

- arrancar o servidor, criar uma tarefa de demonstração e ver o evento no ecrã em menos de 1 s;
- filtrar por `correlation_id` e por nível;
- pedido sem token recusado; pedido com *Origin* inválido recusado; servidor só em `127.0.0.1`;
- reiniciar o servidor: o histórico persiste;
- a interface funciona offline (CSS compilado localmente, sem CDN);
- capturas de ecrã guardadas como evidência.

**Demonstração:** abrir o browser, enviar uma mensagem no chat e ver os eventos a correr em tempo real.

**Gate:** todos os ecrãs com dados reais; testes de segurança local a passar.

**Recuperação:** o frontend é descartável; o núcleo não depende dele.

### Fase 4 — MVP vertical: CREATE ponta a ponta

**Objectivo:** o primeiro fluxo completo. Pedido em texto → Concierge → requisitos → plano → arquitectura → aprovação na interface → Construtor gera um módulo com teste → Testador executa → Revisor valida → relatório.

**Activa:** `create_flow`, agentes em Markdown, `persona`, aprovações na UI.

**Nota de segurança:** usa-se um executor mínimo (processo filho, ambiente limpo, pasta temporária, *timeout*, sem credenciais), declarado como **não isolado**. Só corre com aprovação explícita e é substituído na Fase 6.

**Ficheiros:** `agents/definitions/*.md` (um por agente), `agents/runner/`, `workflows/create/`, `schemas/` (um por esquema), `approvals/tokens/`, `execution/simple_runner.py`, `reports/final_report.py`, `persona.md`; ecrã «Equipa de agentes».

**Testes reais:**

- caso dourado: «cria uma calculadora de linha de comandos com testes» → ficheiros gerados e `pytest` aprovado;
- repetido com Gemini e, em modo degradado, verificando que o Ollama não assume a geração de código;
- saída inválida de um agente rejeitada e repetida com limite;
- **aprovação não forjável:** um agente que devolva `approved=true` não consegue aprovar nada; sem token da UI, nada é aplicado;
- cancelar a meio; matar e retomar;
- cabeçalho de um agente Markdown inválido é recusado com mensagem clara;
- harness de avaliação com 5 casos de referência pontuados.

**Demonstração:** pedir uma pequena aplicação no chat, aprovar o plano e ver os agentes trabalhar.

**Gate:** 5 casos de referência acima da pontuação mínima; recuperação após *kill*; relatório final gerado.

**Recuperação:** cada fluxo grava *checkpoint* por estágio; retoma-se do último estágio concluído.

### Fase 5 — Workspace seguro, ZIP, Chat com anexos, diff e snapshots

**Objectivo:** dar poder de escrita aos agentes sem perder o controlo. Primeiro a segurança, depois a capacidade.

**Activa:** `workspace_write`, snapshots, diff, ZIP, Permissões, anexos no Chat.

**Ficheiros:** `workspace/paths/` (canonicalização), `symlinks.py`, `scanner/`, `sensitive.py`, `archive/` (ZIP), `snapshot/`, `rollback.py`, `audit/`, `file_ops.py`; `approvals/diff/`; `ui/web/attachments.js`; ecrãs «Aprovações e diff», «Snapshots», «Permissões».

**Testes reais (pasta temporária real):**

- *path traversal*, caminhos absolutos, nomes reservados do Windows, caminhos longos;
- *symlink* a apontar para fora do workspace bloqueado;
- ZIP malicioso: *Zip Slip*, ZIP bomb (limites de tamanho e rácio), ZIP com *symlinks*, ZIP dentro de ZIP além do limite de profundidade;
- **cobertura do chat:** pasta com 5 níveis de subpastas, nomes com acentos e ZIP interno — o número de ficheiros lidos mais os ignorados tem de bater com o disco, e cada ignorado tem motivo;
- ficheiros sensíveis detectados e marcados como proibidos de seguir para a cloud;
- anexos entram em quarentena e só passam ao workspace após aprovação;
- snapshot → alterar → rollback devolve o estado idêntico (comparação de *hashes*); Undo da última alteração;
- interrupção durante operação de ficheiros: o rollback deixa a pasta consistente;
- ecrã de diff: aprovar/rejeitar por bloco e verificar o resultado no disco.

**Demonstração:** largar um ZIP com subpastas no chat, ver o relatório de cobertura, aprovar e desfazer.

**Gate:** bateria de segurança a 100%; rollback comprovado; nenhuma escrita fora do workspace em qualquer teste.

**Recuperação:** snapshot automático antes de cada alteração; a eliminação é sempre reversível (quarentena).

### Fase 6 — Execução isolada

**Objectivo:** substituir o executor mínimo por isolamento a sério.

**Activa:** `sandbox_exec`.

**Passos:** comparar Docker, WSL, ambiente virtual com restrições e Windows Sandbox (apenas Pro/Enterprise; o Docker Desktop tem restrições de licença em contexto comercial). Implementar o contrato `Executor` com um adaptador por mecanismo; o sistema escolhe o melhor disponível e **recusa executar** se não houver nenhum seguro.

**Ficheiros:** `execution/executors/contract.py`, `docker.py`, `venv.py`; `limits/`, `capture/`, `cleanup/`; ecrã «Testes e execução».

**Testes reais:**

- código que tenta ler um ficheiro fora da pasta, abrir a rede ou ler variáveis de ambiente com credenciais **falha**;
- ciclo infinito termina no *timeout*; consumo excessivo de memória é cortado;
- *stdout/stderr* capturados e mostrados na interface;
- não ficam processos nem contentores órfãos;
- scripts dentro de um ZIP **nunca** correm automaticamente;
- sem mecanismo seguro disponível, o sistema recusa e explica.

**Demonstração:** correr um programa malicioso de teste e ver cada tentativa de fuga bloqueada e registada.

**Gate:** testes de fuga todos bloqueados; sem processos órfãos.

**Recuperação:** cada execução ocorre numa cópia; o workspace original não é tocado.

### Fase 7 — Project Intelligence (ANALYZE) e painel de análise de código

**Objectivo:** compreender projectos existentes sem enviar tudo ao LLM.

**Activa:** `analysis`.

**Ficheiros:** `analysis/scanners/` (`language_detect.py`, `entrypoints.py`, `dependencies.py`, `duplicates.py`, `unused.py`), `graph/import_graph.py`, `quality/` (Ruff, mypy, Bandit, pip-audit), `context_selector.py` (escolhe só o contexto relevante, dentro do orçamento de tokens), `risk_report.py`; verificação de citações em código para relatórios do Planeador; ecrã «Análise de código».

**Testes reais:**

- analisar o próprio HybridCrewAI e comparar com o `MAP.md`;
- projectos de teste em `tests/fixtures/` com defeitos plantados (ciclo de imports, código duplicado, segredo exposto, dependência vulnerável) — todos têm de ser encontrados;
- comentários com *prompt injection* não alteram o comportamento do agente;
- o seleccionador de contexto respeita o orçamento de tokens;
- uma citação inventada num relatório é detectada pela verificação em código.

**Demonstração:** analisar um projecto no chat e navegar pelo grafo e pelos achados por severidade.

**Gate:** defeitos plantados detectados (mínimo acordado); relatório técnico gerado e visualizado.

**Recuperação:** a análise é só de leitura; não altera nada.

## 12. Fichas de fase (8 a 14)

### Fase 8 — IMPROVE e controlo de versões (Git)

**Objectivo:** melhorar projectos existentes de forma pequena, verificável e reversível.

**Activa:** `improve_git` (autonomia até L2).

**Ficheiros:** `workflows/improve/`, `change/planner.py`, `impact.py`, `executor.py`, `batch.py`, `validator.py`; `git/detect.py`, `status.py`, `branches.py`, `commits.py`, `diff.py`; ecrã «Git e alterações».

**Regras:** um ramo de trabalho e um *commit* por tarefa; nunca sobrescrever alterações não guardadas do utilizador (recusa e avisa).

**Testes reais:**

- repositório Git real temporário: o sistema cria ramo, aplica alteração, corre testes e faz *commit*;
- repositório com alterações não guardadas: recusa tocar nos ficheiros afectados;
- refactorização de um projecto-fixture: os testes do projecto continuam a passar;
- reverter a tarefa devolve o estado inicial.

**Demonstração:** pedir uma melhoria a um projecto, rever o diff, aprovar e ver o *commit*.

**Gate:** nenhuma perda de dados do utilizador em todos os cenários.

**Recuperação:** snapshot + ramo; reverter é um comando.

### Fase 9 — Autonomia, tarefas em segundo plano e rotinas (MAINTAIN)

**Objectivo:** agentes a trabalhar sozinhos com limites, e um assistente proactivo.

**Activa:** `background_tasks`, rotinas, horas de silêncio, orçamentos, centro de comando (L2; L3 só com testes).

**Ficheiros:** `autonomy/budgets/`, `checkpoints/`, `resume.py`, `kill_switch.py`; `routines/engine.py`, `schedule.py`, `quiet_hours.py`, `late_policy.py`; ecrãs «Custos, quotas, rotinas» e «Centro de comando».

**Regras:**

- cada passo é gravado; uma tarefa interrompida três vezes falha em vez de repetir para sempre;
- quando o orçamento acaba, o último passo não tem ferramentas e pede a escrita do resultado (parar não é perder o trabalho);
- sem quota, a tarefa fica em pausa e retoma sozinha;
- uma rotina que vence enquanto o sistema está desligado espera enquanto ainda fizer sentido e depois é saltada, com registo;
- não retomar operações destrutivas sem verificar o estado; não repetir operações não idempotentes.

**Testes reais:**

- tarefa longa com passos reais interrompida por *kill*, reinício e retoma sem repetir passos;
- orçamento de tokens/tempo/iterações esgotado → pausa e pedido de aprovação, com resultado parcial guardado;
- botão de paragem durante a geração de ficheiros deixa tudo consistente;
- tarefa interrompida três vezes passa a FAILED;
- rotinas: criar, alterar por texto, vencer durante o silêncio e verificar a política de atraso e as horas de silêncio;
- duas tarefas em projectos diferentes não misturam dados.

**Demonstração:** «faz isto durante dez minutos», continuar a conversar e receber o aviso no fim.

**Gate:** nível L2 validado; L3 só se todos os testes de orçamento e paragem passarem.

**Recuperação:** *checkpoints* por passo; relatório de sessão com o ponto exacto de interrupção.

### Fase 10 — Memória e conhecimento

**Objectivo:** o assistente lembra-se de decisões e contexto, projecto a projecto.

**Activa:** `memory`.

**Abordagem:** SQLite + FTS5 primeiro. Embeddings/pesquisa vectorial só se se provar que a pesquisa textual é insuficiente. O prompt leva um núcleo (identidade e factos recentes, com orçamento) e um **índice das chaves** que não couberam, para o modelo saber que existem; o resto vai-se buscar por uma ferramenta `recall_memory`.

**Ficheiros:** `knowledge/store/`, `project_memory.py`, `engineering_memory.py`, `session_memory.py`, `search/`, `retention.py`; ecrã «Memória» com ver e apagar.

**Testes reais:**

- guardar uma decisão, reiniciar, e o agente cita-a ao planear;
- a memória do projecto A nunca aparece no projecto B;
- um facto fora do núcleo é encontrado por `recall_memory` graças ao índice de chaves;
- eliminar funciona e deixa de ser recuperável;
- segredos não são guardados na memória.

**Demonstração:** perguntar «o que decidimos sobre X?» numa sessão nova.

**Gate:** isolamento entre projectos a 100%; recuperação relevante nos casos de referência.

**Recuperação:** cópia da base de conhecimento antes de cada migração.

### Fase 11 — Voz JARVIS (Gemini Live)

**Objectivo:** falar com o assistente e ouvi-lo em português de Portugal.

**Activa:** `voice`.

**Abordagem:** a voz é uma camada separada, desacoplada dos agentes de engenharia, assente no **Gemini Live**. O STT/TTS local (faster-whisper ou whisper.cpp; Piper com vozes pt\_PT) fica como modo opcional offline, depois de testada a qualidade. A voz acompanha o idioma falado; o Concierge usa a persona.

**Ficheiros:** `voice/live/` (sessão, retoma de sessão, instruções), `stt/`, `tts/`, `session.py`, `commands.py`, `interrupt.py`, `devices.py`, `push_to_talk.py`, `echo_guard.py`, `wake_word.py` (opcional); ecrã «Voz».

**Testes reais:**

- áudios gravados com frases em PT-PT (incluindo «cancela a tarefa») com taxa de acerto mínima acordada;
- latência de ponta a ponta medida e registada;
- interrupção: falar enquanto o assistente fala corta a síntese e cancela ou ajusta a tarefa;
- guarda contra eco: o assistente não responde à sua própria voz;
- teste de microfone com medidor e escolha de dispositivos por nome;
- uma ligação interrompida não apaga a conversa;
- a voz não bloqueia um *workflow* em curso;
- sem rede, o modo degradado avisa e passa ao texto ou à voz local, se instalada.

**Demonstração:** pedir uma tarefa por voz, interromper e receber o progresso falado.

**Gate:** metas de acerto e latência cumpridas; modo texto equivalente.

**Recuperação:** a sessão guarda o estado; a voz pode falhar sem afectar as tarefas.

### Fase 12 — Controlo do computador e ferramentas

**Objectivo:** o assistente actua no computador (abrir aplicações, volume, janelas, atalhos) de forma verificável e segura.

**Activa:** `computer_control`; todas as acções exigem confirmação ou são reversíveis.

**Regras:**

- cada ferramenta tem parâmetros tipados e devolve `ToolResult` com evidência real (abrir uma aplicação observa a tabela de processos; volume e brilho são lidos de volta);
- **nunca** shell com texto do modelo e **nunca** código escrito pelo modelo e executado;
- acções irreversíveis (desligar, reiniciar, rede) esperam um botão que o utilizador carrega;
- fechar uma aplicação é por nome, pedindo educadamente, com triplo cuidado para nunca fechar o próprio assistente;
- quando o sistema não permite uma acção (por exemplo Wayland ou permissões do macOS), o assistente di-lo em vez de fingir;
- ferramentas de um só ficheiro, com descoberta automática e permissões mínimas; avaliar o MCP para ferramentas externas;
- **ferramentas de redes (P-02):** se confirmadas, só de leitura, com lista de destinos permitidos e permissão de rede própria.

**Ficheiros:** `tools/registry/`, `tools/computer/open_app.py`, `volume.py`, `windows.py`, `close_app.py`, `confirm.py`, `platform_guard.py`, `network/` (condicional).

**Testes reais:**

- abrir uma aplicação inexistente devolve `failed`, e nunca `done`;
- uma tentativa de injecção de comandos num nome de aplicação não executa nada;
- fechar por nome nunca atinge os processos do assistente;
- volume: pedir um nível define o nível, pedir um passo muda o passo, e ambos são lidos de volta;
- sem o botão de confirmação, desligar não acontece;
- em sessão sem permissão, o resultado é `unverified` ou `failed` com explicação.

**Demonstração:** «abre o editor e baixa o volume», com o estado verificado visível no ecrã.

**Gate:** bateria de segurança de ferramentas a 100%; nenhuma acção reportada como feita sem verificação.

**Recuperação:** Undo para o que for reversível; registo de auditoria de todas as acções.

### Fase 13 — Engenharia reversa (extensão REA via MCP)

**Objectivo:** analisar binários, aplicações sem código-fonte, Electron e APK, como extensão opcional do modo ANALYZE.

**Activa:** `reverse_eng`.

**Cuidados:** origem oficial (`morluto/rea`, `rea.tools` ou pacote npm `rea-agents`; existem cópias e *forks*) com versão fixada; o REA corre como processo separado (requer Node.js 22 ou superior); a instalação de ferramentas pede aprovação explícita; análise de binários desconhecidos só no sandbox, sem rede e sem credenciais; o resultado extraído é dado não confiável; as raízes de entrada ficam limitadas ao workspace autorizado; aviso legal e registo da finalidade antes de analisar (software próprio, código aberto, malware, interoperabilidade ou com autorização).

**Testes reais:**

- binário inofensivo compilado por nós (e uma app JavaScript pequena): o REA lista funções e produz evidência em relatório;
- tentativa de analisar um ficheiro fora do workspace bloqueada;
- instalação sem aprovação recusada;
- binário com *prompt injection* nas strings não altera o comportamento do agente;
- corre sem rede, dentro do sandbox, sem deixar processos órfãos.

**Gate:** testes de isolamento a 100%; contrato `Tool` isola o resto do sistema de mudanças de versão do REA.

### Fase 14 — Avaliação contínua, documentação e distribuição

**Objectivo:** fechar o produto.

**Entregas:** harness de avaliação com 20 ou mais casos e comparador entre modelos e prompts; documentação automática em Markdown e HTML, com diagramas gerados de forma determinística a partir de dados estruturados; instalador, actualizações e migração de dados; testes reais em Windows e Linux; desinstalação limpa; manual de utilização.

**Testes reais:**

- instalação limpa em máquina nova nos dois sistemas;
- actualização com migração de dados e recuperação se falhar a meio;
- desinstalação sem resíduos;
- comparar dois modelos nos casos de referência e detectar a regressão de um prompt alterado.

**Gate final:** instalação limpa → criar, analisar e melhorar um projecto, por texto e por voz, com todos os *gates* anteriores verdes.

## 13. Skills do projecto

Em vez de uma Skill gigante, há **várias Skills pequenas**, cada uma com um `SKILL.md` curto (menos de 100 linhas), *frontmatter* YAML (`name`, `description`) e referências carregadas só quando necessário (*progressive disclosure*). O mesmo conteúdo serve o Codex e o OpenCode; dentro do HybridCrewAI, um adaptador carrega as Skills como instruções dos agentes. **Uma Skill é só texto e não impõe nada:** quem impõe são os `scripts/`. As permissões reais continuam a ser dos serviços determinísticos.

| Skill | Quando se usa | Conteúdo principal | Script de apoio |
| --- | --- | --- | --- |
| `hcw-router` | Sempre; porta de entrada | Escolhe a Skill certa, regras globais curtas, onde estão `STATE.md` e `tasks.yaml` | `lint_skills.py` |
| `hcw-handoff` | Início e fim de cada sessão | Lê `STATE.md` e `DEVLOG.md` ao começar; actualiza-os ao terminar, com a próxima acção exacta | `sync_state.py` |
| `hcw-ideas-intake` | Quando surge uma ideia nova | Regista em `IDEAS.md` com estado, fase e motivo antes de se perder | `check_ideas.py` |
| `hcw-audit` | Fase 0 e antes de mexer em módulos | Como inventariar, classificar e preencher o relatório | `inventory.py` |
| `hcw-plan` | Criar ou actualizar tarefas | Modelo de tarefa, IDs `HCW-FF-NNN`, dependências, requisitos | `validate_plan.py` |
| `hcw-implement` | Implementar tarefas aprovadas | Alteração mínima, ficheiros pequenos, README.txt, `module.yaml` | `check_file_size.py`, `check_modules.py` |
| `hcw-test-gate` | Fechar tarefas e fases | Como correr `hcw accept`, ler o relatório, anexar evidências | `run_gate.py` |
| `hcw-security-review` | Workspace, execução, egress, ferramentas | Lista de verificação de segurança e ataques a testar | `check_threats.py` |
| `hcw-docs` | Documentar | Padrão PT-PT, modelos de README, ADR e relatórios | `check_docs.py` |

**Estrutura:**

```text
skills/
  hcw-router/            SKILL.md
  hcw-handoff/           SKILL.md  templates/STATE_TEMPLATE.md
  hcw-ideas-intake/      SKILL.md  templates/IDEA_TEMPLATE.md
  hcw-audit/             SKILL.md  references/  templates/WORKSPACE_AUDIT_TEMPLATE.md
  hcw-plan/              SKILL.md  templates/TASK_TEMPLATE.md  REQUIREMENT_TEMPLATE.md
  hcw-implement/         SKILL.md  references/CODING_RULES.md  templates/MODULE_TEMPLATE.md
  hcw-test-gate/         SKILL.md  scripts/run_gate.py  templates/TEST_REPORT_TEMPLATE.md
  hcw-security-review/   SKILL.md  references/ATTACK_CHECKLIST.md
  hcw-docs/              SKILL.md  templates/ADR_TEMPLATE.md  DOCUMENTATION_STANDARD.md
scripts/                 validate_plan.py  check_traceability.py  sync_plan.py
                         check_file_size.py  check_modules.py  lint_skills.py
```

**Regras de uso:**

- ler `STATE.md` e o `tasks.yaml` antes de iniciar trabalho; nunca reescrever o plano inteiro por conveniência, apenas fazer alterações localizadas;
- registar decisões em ADR; nunca apagar tarefas concluídas (se forem substituídas, ficam DEPRECATED e ligadas à nova);
- distinguir sempre proposta de implementação validada;
- as Skills não concedem permissões: ter acesso às instruções não dá acesso ao sistema de ficheiros.

## 14. Mecanismos de continuidade e controlo

O objectivo é que nada se perca entre sessões, ferramentas (Codex, OpenCode, HybridCrewAI) ou conversas.

### 14.1 `tasks.yaml` — fonte única de verdade

O estado do plano vive em formato máquina; o `MASTER_PLAN.md` é gerado a partir dele por `sync_plan.py`, para não existirem cópias que divergem.

```yaml
- id: HCW-02-004
  title: Implementar escada de modelos com cooldown
  phase: 2
  status: PLANNED        # NOT_STARTED RESEARCH PLANNED APPROVED IN_PROGRESS BLOCKED
                         # IMPLEMENTED TESTING VALIDATED REJECTED DEPRECATED
  priority: critical
  requirements: [FR-012, NFR-004]
  depends_on: [HCW-02-001, HCW-01-006]
  modules: [llm/router]
  files_new: [app/llm/router/ladder.py, app/llm/router/cooldown.py]
  files_change: []
  tests: [tests/unit/test_ladder.py, tests/integration/test_fallback_matrix.py]
  acceptance: ["Cooldown difere por tipo de erro", "Toda a chamada tem timeout"]
  evidence: []           # preenchido só com relatório do gate
  validated_on: null
```

Uma tarefa só passa a `VALIDATED` quando os critérios de aceitação estão cumpridos **e** existe evidência anexada. O `validate_plan.py` verifica estados válidos, IDs únicos, pré-requisitos concluídos e requisitos existentes.

### 14.2 `STATE.md`

Uma página, sempre actual:

```markdown
# Estado do projecto
Fase actual: 2 · Gate: pendente
Última tarefa validada: HCW-02-003 (2026-12-02)
A meio: HCW-02-004 (ladder.py escrito, falta teste de cooldown)
Bloqueios: nenhum
Próxima acção exacta: escrever tests/unit/test_cooldown.py (caso 429 vs 504)
Decisões pendentes: P-04 hardware
```

### 14.3 `DEVLOG.md`

Diário curto e datado, uma entrada por sessão: o que se fez, o que falhou, o que ficou por fazer, ficheiros tocados, comandos de teste executados e resultado.

### 14.4 `IDEAS.md`

Caixa de ideias com estado `PROPOSTA`, `APROVADA`, `ADIADA` ou `REJEITADA`, fase associada e motivo. Nenhuma ideia entra no plano sem passar por aqui e sem aprovação; as aprovadas viram tarefas em `tasks.yaml`.

### 14.5 ADR

`docs/adr/ADR-NNNN-titulo.md`, com contexto, problema, alternativas, decisão, justificação, consequências e estado. ADRs obrigatórios nesta fase de planeamento: motor de agentes (0001), LiteLLM versus SDK nativo (0002), tecnologia de isolamento (0003), política cloud e egress (0004), tecnologia de UI (0005).

### 14.6 Protocolo de sessão

1. **Ao começar:** a Skill `hcw-handoff` lê `STATE.md`, as últimas entradas do `DEVLOG.md` e as tarefas disponíveis; confirma pré-requisitos.
2. **Durante:** uma tarefa de cada vez; alteração mínima coerente; testes específicos e depois a suite relevante.
3. **Ao terminar:** actualiza `tasks.yaml` (só com evidência), `STATE.md` e `DEVLOG.md`; regista ideias novas em `IDEAS.md`; *commit* com o ID da tarefa.
4. **Ao fechar uma fase:** `hcw accept --phase N`, relatório em `reports/`, etiqueta Git `phase-NN-go`.

## 15. Requisitos e rastreabilidade

Tipos de requisito: **FR** (funcional), **NFR** (não funcional), **SEC** (segurança), **OPS** (operacional), **UI** (interface), **DOC** (documentação). Cadeia obrigatória:

```text
Requisito → Funcionalidade → Módulo → Ficheiro → Teste → Evidência
```

Exemplo: `SEC-004` (protecção contra *path traversal*) → `workspace/paths` → `canonicalize.py` → `test_paths_traversal.py` → relatório de segurança da Fase 5. O `check_traceability.py` falha se um requisito obrigatório não tiver teste ou evidência, ou se desaparecer do plano sem decisão registada.

## 16. Modelo de ameaças

| Ameaça | Fase | Contramedida | Teste |
| --- | --- | --- | --- |
| *Prompt injection* em ficheiros, páginas ou binários analisados | 2, 7, 13 | Conteúdo como dados delimitados; agentes sem ferramentas directas; marcador de fecho não forjável | Fixtures com instruções hostis |
| Fuga de segredos para a cloud | 2, 5 | Scan, redacção e exclusão antes do envio; interruptor por projecto | Servidor falso que capta o payload |
| Aprovação forjada pelo modelo | 4, 12 | Token único emitido só pela interface, ligado ao hash do diff | Agente devolve `approved=true` sem efeito |
| ZIP malicioso (Zip Slip, ZIP bomb, *symlinks*) | 5 | Limites, validação de caminhos, quarentena | Arquivos hostis em `fixtures/` |
| *Path traversal* e *symlinks* exteriores | 5 | Canonicalização e workspace como unidade de permissões | Bateria de caminhos |
| Execução de código gerado ou de terceiros | 4, 6 | Isolamento obrigatório; recusa sem mecanismo seguro; sem rede nem credenciais | Testes de fuga |
| Injecção de comandos em ferramentas | 12 | Parâmetros tipados, sem shell, sem código escrito pelo modelo | Nomes com `&` e `;` |
| Fecho da janela ou processo errado | 12 | Correspondência por processos em execução; protecção em três camadas do próprio assistente | Teste de auto-protecção |
| Interface local atacada via browser | 3 | `127.0.0.1`, token de sessão, verificação de *Origin* | Pedidos com *Origin* falso |
| Dependência ou ferramenta comprometida | 0, 13 | Versões fixadas, `pip-audit`, origens oficiais, instalação com aprovação | Verificação no CI |
| Perda de trabalho em falhas | 1, 5, 9 | Snapshots, *checkpoints*, *kill tests* | Testes de recuperação |
| Custos e quotas fora de controlo | 2, 9 | Orçamento por tarefa, pausa por quota, botão de paragem | Esgotar orçamentos de propósito |
| Acção reportada como feita sem o ter sido | 1, 12 | `ToolResult` com verificação; `unverified` nunca é sucesso | Aplicação inexistente |

## 17. Cadeia de fornecimento, credenciais e Windows

- **Dependências:** matriz com nome, versão pretendida e instalada, licença, origem, dependências transitivas e justificação; versões fixadas com ficheiro de bloqueio; `pip-audit` no CI; não introduzir uma biblioteca quando uma existente já cobre a necessidade. Atenção a conflitos de versões entre CrewAI, LiteLLM e qualquer SDK.
- **Credenciais:** no armazenamento seguro do sistema (Credential Manager no Windows, equivalente no Linux), nunca em ficheiros do projecto, nunca em logs, nunca acessíveis ao código testado.
- **Windows:** caminhos longos, nomes sem distinção de maiúsculas, CRLF e LF, ficheiros bloqueados em uso, antivírus a interferir com o sandbox; o Windows Sandbox só existe nas edições Pro e Enterprise e o Docker Desktop tem restrições de licença em contexto comercial; `localhost` pode resolver para `::1` enquanto alguns servidores locais escutam apenas IPv4, por isso os endereços locais são normalizados para `127.0.0.1` e um *proxy* global não deve ser usado para chegar à própria máquina.
- **Termos do Gemini:** confirmar a versão em vigor; activar a facturação antes de enviar código real; os serviços agênticos exigem que não se contornem os pedidos de confirmação humana, o que o nosso desenho respeita.

## 18. Riscos principais

| Risco | Mitigação |
| --- | --- |
| Projecto demasiado grande | Fatias verticais, *gates*, fase N+1 só com GO |
| Agentes a gerar código mau | Revisor, harness de avaliação, testes obrigatórios |
| Dependência exclusiva de um fornecedor cloud | Escada de modelos, Ollama em segundo plano, segunda linha cloud por extensão |
| Quotas e custos do Gemini | Orçamento por tarefa, pausa por quota, registo de utilização |
| Fuga de código e segredos | Egress, facturação activa, interruptor por projecto |
| Poder excessivo (escrita, execução, controlo do computador) | Ordem das fases: segurança antes de capacidade; autonomia por níveis |
| Perda de contexto entre sessões | `STATE.md`, `DEVLOG.md`, `tasks.yaml`, Skill `hcw-handoff` |
| Ficheiros enormes e difíceis de manter | Limite de 300 linhas por script, `MAP.md`, `module.yaml` |
| Qualidade da voz em PT-PT | Testes com áudios reais antes de qualquer compromisso |
| Mudanças de versão de modelos e ferramentas | Configuração e adaptadores isolados; contrato `Tool` e `LiveSession` |

## 19. Caixa de ideias (estado actual)

| ID | Ideia | Estado | Fase |
| --- | --- | --- | --- |
| IDEA-001 | Chat com anexos de pastas, subpastas e ZIP, com relatório de cobertura | Aprovada (em proposta) | 3 e 5 |
| IDEA-002 | Stitch para desenhar ecrãs | Proposta | 3 |
| IDEA-003 | REA (engenharia reversa) como extensão | Proposta, aguarda finalidade | 13 |
| IDEA-004 | ByteByteGo como leitura de referência | Adiada (não é ferramenta) | — |
| IDEA-005 | Ferramentas de redes de diagnóstico | A clarificar | 12 |
| IDEA-006 | Persona do assistente | Proposta | 4 |
| IDEA-007 | Resumos e briefings proactivos | Proposta | 9 |
| IDEA-008 | Controlo do computador | Proposta | 12 |
| IDEA-009 | Acesso pelo telemóvel com emparelhamento | Adiada | Após 14 |
| IDEA-010 | Domótica e dispositivos | Fora de âmbito por agora | — |

## 20. Glossário, acrónimos e histórico

**ADR:** Architecture Decision Record. **Egress:** tudo o que sai do sistema para fora (por exemplo, para a cloud). **Gate:** ponto de controlo de uma fase, com GO ou NO-GO. **HUD:** interface de estado em ecrã. **MCP:** Model Context Protocol. **REA:** Reverse Engineer Anything. **SSE:** Server-Sent Events. **STT/TTS:** reconhecimento e síntese de voz. **Quarentena:** área onde ficam os anexos até serem analisados e aprovados. **ToolResult:** resposta normalizada de uma ferramenta, com estado e evidência.

**Histórico de versões:** 1.0.0 — Plano Mestre e Skill originais; 2.0 — fatias verticais, interface web e gates; **3.0.0 — este relatório:** Gemini Live como principal, Ollama em segundo plano, lições do Mark LVII, Chat com anexos, Stitch, REA, controlo do computador e mecanismos de continuidade.

## 21. Próximos passos

1. **Rever e aprovar** este relatório e as decisões D-04 a D-13.
2. **Gerar os ficheiros reais** em pastas pequenas e documentadas: as nove Skills, `tasks.yaml` com todas as tarefas `HCW-FF-NNN` por fase, `STATE.md`, `DEVLOG.md`, `IDEAS.md`, `THREAT_MODEL.md`, os modelos e os `scripts/` de validação.
3. **Responder às pendências** P-02 a P-05 (redes, finalidade do REA, hardware, tipo de conta Gemini).
4. **Arrancar a Fase 0** com a auditoria do código existente; para isso é preciso ver a estrutura real do projecto.
