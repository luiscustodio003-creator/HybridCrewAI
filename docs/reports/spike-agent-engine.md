# HCW-00-009 — Spike do motor de agentes

Data: 2026-11-22 · Tarefa: `HCW-00-009` · Requisitos: `NFR-003`, `NFR-004`

## Objectivo e limites

Comparar três caminhos para o motor de agentes do HybridCrewAI: núcleo próprio, CrewAI e LangGraph. O cenário é idêntico nos três casos: pedido, plano, pausa para aprovação, morte do processo e retoma.

Este spike é documental. Não foram instalados CrewAI, LiteLLM nem LangGraph; não foi executado código dos candidatos; não foram medidos tempos de arranque nem contadas linhas de código reais. Todos os números da tabela são faixas indicativas e estão marcados como tal. A decisão final pertence ao utilizador e será registada em `ADR-0001` pela tarefa `HCW-00-010`.

## Fontes oficiais consultadas

- CrewAI Flows: https://docs.crewai.com/concepts/flows
- CrewAI — Human Feedback in Flows: https://docs.crewai.com/en/learn/human-feedback-in-flows
- CrewAI — Human-in-the-Loop: https://docs.crewai.com/en/learn/human-in-the-loop
- LangGraph — Interrupts: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- LangGraph — Persistence: https://langchain-ai.github.io/langgraph/concepts/persistence
- LangGraph — Graph API (reexecução e idempotência): https://langchain-ai.github.io/langgraph/concepts/low_level

## Cenário comum

| Passo | Acção esperada | Prova de que o passo correu |
|---|---|---|
| Pedido | Receber um pedido com `task_id` e `correlation_id`, sem executar texto do modelo | Evento `request.accepted` com estado persistido |
| Plano | Gerar três passos: interpretar, planear, propor acção | Evento `plan.created`; plano guardado no estado |
| Pausa | Parar antes da acção irreversível e exigir aprovação | `approval.required`; token emitido só pela interface |
| Morte do processo | Encerrar o processo depois do checkpoint da pausa | Último checkpoint recuperável pelo mesmo `task_id` |
| Retoma | Carregar o estado, validar o token e continuar | Evento `resumed`; nenhuma acção já confirmada é repetida |

Regras transversais do cenário: conteúdo externo é dado, nunca comando; `ToolResult` só é `done` após verificação; segredos não entram no estado nem em logs; a retoma usa o mesmo identificador de tarefa.

## Núcleo próprio

Mecanismo: máquina de estados explícita, log de eventos em SQLite e checkpoint após cada transição. O estado mínimo inclui `task_id`, `correlation_id`, `phase`, `agent`, `status`, `pending_approval_token_hash`, `last_completed_step` e `version`.

- Pedido: handler de comando valida o tipo do pedido e grava `request.accepted`.
- Plano: gerador de plano produz passos tipados; o modelo nunca escolhe directamente um comando.
- Pausa: transição `PLANNING → WAITING_APPROVAL`; apenas a interface emite o token de aprovação.
- Morte do processo: o último checkpoint commitado é a fonte da verdade.
- Retoma: carregar checkpoint, comparar hash do token, continuar em `EXECUTING`; idempotência por chave por passo.

Vantagens: controlo total sobre o contrato de eventos, aprovação e persistência; nenhuma dependência externa; compatibilidade Windows/Linux resolve-se com SQLite e pathlib. Desvantagens: é preciso implementar e testar tudo, incluindo concorrência, replay, expiração de checkpoints e limites de tamanho.

Dependências previstas: apenas biblioteca padrão (`asyncio`, `dataclasses`, `sqlite3`, `uuid`, `hashlib`, `signal`). Faixa indicativa de código: 600–1000 linhas para um MVP robusto, não medida. Arranque: baixo, não medido. Facilidade de retoma: alta se o desenho for seguido, mas todo o trabalho é interno.

## CrewAI

A documentação oficial descreve Flows com estado próprio (dict ou Pydantic), identificador UUID automático, persistência SQLite por omissão e recuperação de estado após falhas/reinícios. O decorator `@human_feedback` existe a partir de CrewAI `1.8.0`; pausa o fluxo, recolhe feedback e pode encaminhar outcomes para listeners. Para integrações assíncronas, a documentação mostra `HumanFeedbackPending`, estado persistido automaticamente, `Flow.from_pending(flow_id)` e `flow.resume(feedback)` / `resume_async(feedback)`.

- Pedido: `Flow.kickoff()` com `inputs` contendo o identificador da sessão/tarefa.
- Plano: método `@start()` ou `@router()` com estado tipado.
- Pausa: `@human_feedback` ou provider assíncrono; a aprovação da interface tem de ser adaptada ao provider, sem aceitar `approved=true` vindo do modelo.
- Morte do processo: dependerá do backend de persistência e do ponto em que o estado foi gravado; a documentação afirma recuperação de estado, mas não medida neste spike.
- Retoma: `restore_from_state_id` / `inputs["id"]` para fluxos persistidos, ou `from_pending` + `resume` para feedback pendente.

Vantagens: abstracções prontas para estado, fluxo e feedback humano; menos código de framework. Desvantagens: dependência pesada, versão mínima `1.8.0` para `@human_feedback`, alguma lógica de routing com LLM quando se usa `emit`, e necessidade de adaptar a política de segurança do projecto por cima do framework.

Dependências previstas: `crewai`, Pydantic para estado estruturado e provider LLM configurado; a lista exacta tem de ser fixada no ADR, sem instalação neste spike. Faixa indicativa de código: 150–350 linhas, não medida. Arranque: médio a alto, não medido. Facilidade de retoma: média-alta, condicionada ao backend de persistência e à versão fixada.

## LangGraph

A documentação oficial define `interrupt()` como pausa dinâmica dentro de um nó, com estado guardado pelo checkpointer e retoma via `Command(resume=...)`. O `thread_id` é o cursor persistente. A documentação de persistência distingue checkpointer (estado de curto prazo por thread, HITL, time travel e tolerância a falhas) de store (memória de longo prazo entre threads). A referência de checkpoints lista `InMemorySaver` apenas para testes/depuração e `SqliteSaver` / `PostgresSaver` para opções duráveis. A documentação também avisa que a retoma volta a um limite de checkpoint e reexecuta os passos até à pausa; trabalhos não determinísticos e efeitos colaterais devem ficar em `tasks`.

- Pedido: `graph.invoke(input, config={"configurable": {"thread_id": task_id}})`.
- Plano: nós `StateGraph` ou `@entrypoint` da Functional API.
- Pausa: `interrupt()` no nó de aprovação, com payload JSON serializável.
- Morte do processo: o checkpointer durável guarda o estado no limite do superstep.
- Retoma: mesmo `thread_id` com `Command(resume=...)`; acções já confirmadas precisam de idempotência própria.

Vantagens: primitivas explícitas e bem documentadas para pausa, checkpoint, retoma e time travel; bom ajuste para `NFR-004`. Desvantagens: disciplina de reexecução e efeitos colaterais; crescimento de checkpoints; dependência de checkpointer durável e de um identificador de thread estável.

Dependências previstas: `langgraph`, pacote de checkpointer (`langgraph-checkpoint-sqlite` ou `langgraph-checkpoint-postgres`); versões por fixar no ADR. Faixa indicativa de código: 250–500 linhas, não medida. Arranque: médio, não medido. Facilidade de retoma: alta se os efeitos colaterais estiverem isolados em `tasks`.

## Tabela comparativa

Valores de código e arranque são estimativas documentais, não medições.

| Critério | Núcleo próprio | CrewAI | LangGraph |
|---|---|---|---|
| Linhas de código (estimativa) | 600–1000 | 150–350 | 250–500 |
| Dependências | biblioteca padrão | crewai, Pydantic, provider LLM | langgraph, checkpointer durável |
| Tempo de arranque (estimativa) | baixo | médio-alto | médio |
| Facilidade de retoma | alta, se implementada | média-alta | alta, se os efeitos forem idempotentes |
| Pausa/aprovação | FSM + token da UI | `@human_feedback` / provider | `interrupt()` + `Command(resume=...)` |
| Morte do processo | checkpoint próprio | persistência do Flow / pending | checkpointer por `thread_id` |
| Controlo de segurança | total | adaptar framework | adaptar framework |
| Risco principal | mais código e testes | dependência e versão do framework | reexecução e efeitos colaterais |

## Revisão de segurança

| Ameaça | Contramedida neste spike | Teste | Resultado |
|---|---|---|---|
| Dependência comprometida (fases 0 e 13) | Nenhuma instalação; apenas documentação oficial | Sem teste de execução neste spike; versões e `pip-audit` ficam para o ADR/CI | Sem exposição |
| Aprovação forjada pelo modelo (fases 4 e 12) | Cenário exige token emitido só pela interface | Teste de `approved=true` sem efeito fica para a Fase 4 | Requisito transportado |
| Perda de trabalho em falhas (fases 1, 5 e 9) | Comparação de checkpoint, pending flow e checkpointer | Teste de kill real fica para a Fase 1 | Não medido |
| Fuga de segredos para a cloud (fases 2 e 5) | Não foi enviado conteúdo do projecto; nenhuma credencial usada | Sem payload de teste neste spike | Sem segredos no relatório |
| Execução de código de terceiros (fases 4 e 6) | Não foi instalado nem executado código dos candidatos | Não aplicável neste spike | Sem exposição |

## Leitura preliminar (não é decisão)

- CrewAI oferece o caminho mais curto para pausa e aprovação, mas introduz uma dependência grande e exige adaptar a sua política de aprovação à regra do projecto.
- LangGraph oferece as primitivas mais claras para retoma durável, mas obriga a desenhar idempotência e isolamento de efeitos colaterais desde cedo.
- O núcleo próprio dá controlo total e dependências mínimas, ao custo de mais código e responsabilidade de testes.
- Para `ADR-0001`, o utilizador deve decidir se prefere controlo máximo (núcleo próprio), velocidade de implementação (CrewAI) ou retoma madura (LangGraph).

Perguntas em aberto para o ADR: aceitar dependências externas no motor? Exigir checkpointer durável já na Fase 1? A aprovação terá sempre token da UI? Qual o limite aceitável de linhas de código? Será autorizado um spike empírico com instalação?

## Evidência

- Relatório: `docs/reports/spike-agent-engine.md`.
- Documentação oficial listada em «Fontes oficiais consultadas».
- Sem medições locais: nenhuma dependência dos candidatos foi instalada ou executada.
