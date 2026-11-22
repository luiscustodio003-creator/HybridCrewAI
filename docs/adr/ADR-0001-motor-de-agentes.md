# ADR-0001 — Motor de agentes: núcleo próprio com adaptadores

Estado: ACEITE
Data: 2026-11-22

## Contexto

O HybridCrewAI precisa de um motor que execute pedidos até ao resultado, com plano estruturado, pausa para aprovação humana e retoma após morte do processo. A Fase 00 produziu o spike documental `docs/reports/spike-agent-engine.md`, com o mesmo cenário para três candidatos: núcleo próprio, CrewAI e LangGraph.

Os requisitos relevantes são `NFR-003` (motor substituível por adaptadores) e `NFR-004` (recuperação do estado após interrupção do processo). O projecto também exige que texto de modelo nunca vire comando, que a aprovação seja emitida apenas pela interface e que cada ferramenta devolva um `ToolResult` verificado.

O spike foi documental: não foram instalados CrewAI, LiteLLM nem LangGraph, não foram executados tempos de arranque e as linhas de código são faixas indicativas. A decisão é, portanto, uma escolha de arquitectura com evidência documental, não uma medição empírica.

## Problema

Escolher o motor base da Fase 1 sem criar uma dependência irreversível, sem perder o controlo da política de segurança e sem adiar a recuperação de estado após falhas. A escolha tem de funcionar em Windows e Linux, com ficheiros pequenos, documentação em português de Portugal e testes reais.

## Alternativas

### Núcleo próprio

- **Prós:** controlo total do contrato de eventos, da aprovação e do formato de checkpoint; nenhuma dependência de framework; alinhamento directo com `NFR-003` e `NFR-004`; compatibilidade Windows/Linux com biblioteca padrão e SQLite.
- **Contras:** mais código e mais testes a escrever; concorrência, expiração de checkpoints, idempotência e limites de tamanho passam a ser responsabilidade interna.
- **Evidência:** estimativa de 600–1000 linhas para um MVP robusto, não medida; ver `docs/reports/spike-agent-engine.md`.

### CrewAI

- **Prós:** Flows com estado próprio, persistência SQLite por omissão e `@human_feedback` a partir da versão `1.8.0`; menos código de framework; recuperação documentada via `restore_from_state_id` ou `Flow.from_pending(flow_id)`.
- **Contras:** dependência pesada; política de aprovação e conteúdo externo têm de ser adaptados; versão mínima `1.8.0` para feedback humano; arranque médio-alto estimado.
- **Evidência:** documentação oficial de CrewAI citada no spike; nenhuma instalação ou execução local.

### LangGraph

- **Prós:** `interrupt()`, checkpointer durável, `thread_id` e `Command(resume=...)` são primitivas claras para pausa, retoma e *time travel*; bom ajuste para `NFR-004`.
- **Contras:** retoma reexecuta passos até ao checkpoint; exige idempotência e isolamento de efeitos colaterais; acrescenta dependência de checkpointer e disciplina de desenho.
- **Evidência:** documentação oficial de LangGraph citada no spike; nenhuma instalação ou execução local.

## Decisão

Adoptar um **núcleo próprio e fino** como motor de agentes da Fase 1, com as seguintes regras:

1. O núcleo possui a máquina de estados, o registo de eventos e o checkpoint; o modelo produz apenas propostas tipadas, nunca comandos.
2. A aprovação é um token gerado pela interface, ligado ao identificador da tarefa e ao hash do diff; um `approved=true` devolvido pelo modelo não tem efeito.
3. O estado persistido inclui `task_id`, `correlation_id`, `phase`, `agent`, `status`, hash do token pendente, último passo concluído e versão.
4. Cada passo tem uma chave de idempotência; a retoma não repete acções já confirmadas.
5. CrewAI e LangGraph ficam como opções futuras de adaptador atrás de uma porta estável, sem dependência na Fase 1.
6. Nenhuma dependência de framework é instalada enquanto esta ADR não for aceite e as versões não forem fixadas.

## Justificação

O núcleo próprio dá o controlo necessário para impor as regras de segurança do projecto sem depender da política de um framework externo. Também evita adiar `NFR-004`: o formato de checkpoint é desenhado desde o início. A recomendação do utilizador na abertura de `HCW-00-010` foi "núcleo próprio", com CrewAI e LangGraph como adaptadores futuros.

A tabela do spike mostra que CrewAI reduz código inicial, mas acrescenta versão mínima e adaptação de segurança; LangGraph oferece retoma madura, mas obriga a idempotência desde cedo. O núcleo próprio tem maior custo inicial, porém preserva a fronteira "o modelo propõe, o Python executa" com menos superfície externa.

## Consequências

- A Fase 1 terá de implementar o contrato de eventos, a máquina de estados, o log SQLite e os testes de retoma; não poderá delegar essas responsabilidades num framework.
- Adaptadores futuros só serão introduzidos com nova ADR, versões fixadas, `pip-audit` e aprovação explícita.
- Testes obrigatórios na Fase 1: morte do processo depois do checkpoint e retoma com o mesmo `task_id`; tentativa de aprovação forjada pelo modelo; conteúdo externo com instruções hostis tratado como dado; `ToolResult` não verificado nunca reportado como sucesso.
- O checkpoint não pode conter segredos nem texto de credenciais; apenas hashes e referências.
- Se um spike empírico autorizado mostrar que o núcleo próprio ultrapassa o limite aceitável de código ou falha a recuperação, esta ADR deve ser substituída por outra, não alterada silenciosamente.

## Segurança

| Ameaça | Contramedida nesta decisão | Teste na Fase 1 |
|---|---|---|
| Aprovação forjada pelo modelo (fases 4 e 12) | Token emitido só pela interface e ligado ao hash do diff | Modelo devolve `approved=true`; efeito nenhum |
| Injecção em conteúdo externo (fases 2, 7 e 13) | Conteúdo delimitado como dado; sem ferramentas directas | Fixtures com instruções hostis |
| Perda de trabalho em falhas (fases 1, 5 e 9) | Checkpoint commitado antes da acção irreversível | Kill real e retoma com o mesmo `task_id` |
| Acção reportada sem verificação (fases 1 e 12) | `ToolResult` com verificação obrigatória | Ferramenta inexistente; resultado `unverified` |

## Evidência

- `docs/reports/spike-agent-engine.md` — cenário comum, comparação e revisão de segurança.
- `docs/requirements.yaml` — `NFR-003` e `NFR-004`.
- Documentação oficial de CrewAI e LangGraph listada no spike; sem instalação ou execução local.
