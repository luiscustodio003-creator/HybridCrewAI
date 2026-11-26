# Executor simples com aprovação

## Objectivo

Executar um comando aprovado num subprocesso vigiado e não isolado, sem depender de contentores, com aprovação verificável, prazo, cancelamento e pasta temporária dentro do workspace.

## API pública

- `ExecutionRequest`: pedido com tarefa, correlação, hash do diff, token de aprovação, comando, prazo e evento opcional de cancelamento.
- `ExecutionResult`: resultado imutável com `isolated=False`, código de saída, pasta temporária, saída capturada e duração.
- `SimpleRunner.executar`: valida a aprovação e só depois inicia o subprocesso.
- `ExecutionConfigError`: pedido fora do contrato esperado.
- `GUARDA_SUBPROCESSO` e `ambiente_limpo`: mecanismos usados para bloquear rede e reduzir o ambiente.

## Regras

- Um token emitido pela UI local é obrigatório; tarefa, correlação, diff e validade são conferidos antes da execução.
- Sem aprovação válida, o resultado é `FAILED`, nenhum subprocesso é iniciado e `isolated=false` fica registado.
- O subprocesso corre com `cwd` numa pasta `exec-*` criada dentro de `data_dir`, com ambiente mínimo e sem variáveis `HCW_*` de credenciais.
- Para subprocessos Python, um `sitecustomize.py` bloqueia `socket`, resolução de nomes e acesso a ficheiros fora da pasta autorizada e da biblioteca padrão.
- O prazo é aplicado por sondagem; o cancelamento e o tempo limite terminam o processo com `terminate()` e recorrem a `kill()` apenas se necessário.
- Nenhum valor de token é gravado em resultado, evento ou relatório.
- Este executor não é um limite de segurança para binários arbitrários; isolamento forte fica reservado para o executor da Fase 6.

## Eventos emitidos

`execution.iniciado`, `execution.concluido`, `execution.falhado`, `execution.recusado`.

## Testes

- `tests/unit/test_simple_runner.py`
- `tests/security/test_simple_runner.py`
- `tests/security/test_phase04_threats.py`
