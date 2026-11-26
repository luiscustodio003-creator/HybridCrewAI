# Fluxo CREATE com checkpoints

## Objectivo

Percorrer pedido, requisitos, plano, arquitectura, aprovação, execução, revisão e relatório com passos verificáveis, retomada segura e idempotência por passo.

A aprovação depende sempre de um token emitido pelo servidor local autenticado da interface web; `approved=true` vindo do modelo continua a ser apenas uma reivindicação ignorada.

## API pública

- `CreateRequest`: pedido com tarefa, correlação, diff e chaves de idempotência por passo.
- `WorkflowDependencies`: dependências explícitas injectadas na orquestração.
- `CreateWorkflow.executar`: executa passos pendentes ou devolve o resultado já confirmado.
- `Checkpoint`: último passo concluído, estado da tarefa e digest do token pendente.
- `CheckpointStore`: persistência SQLite do checkpoint, cancelamento, recuperação de execuções interrompidas e chaves já registadas.
- Excepções tipadas: `WorkflowError`, `FluxoInativo`, `AprovacaoInvalida`, `EtapaFalhou`, `CheckpointStoreError`.

## Regras

- O valor do token nunca é gravado; o checkpoint guarda apenas SHA-256 hexadecimal.
- Um passo repetido com a mesma chave não publica eventos nem avança o estado.
- A retomada reexecuta apenas etapas ainda não confirmadas.
- `CheckpointStore.cancelar` marca o checkpoint como `CANCELLED` e impede novos passos sem apagar as chaves confirmadas.
- `CheckpointStore.recover_interrupted` transforma checkpoints `RUNNING` em `INTERRUPTED` após a morte do processo.
- Todos os eventos incluem `correlation_id`, `task_id`, `agent` e `phase`.
- O fluxo não inventa APIs nem executa texto de modelo como comando.

## Testes

- `tests/unit/test_create_workflow.py`
- `tests/integration/test_create_workflow_checkpoint.py`
- `tests/recovery/test_create_kill_resume.py`
