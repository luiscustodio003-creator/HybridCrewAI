# Relatório — Caso dourado da calculadora (Fase 4)

Data: 2026-11-25 · Tarefa: HCW-04-008

## Identificação da evidência

| Campo | Valor |
|---|---|
| Resultado da ferramenta | `ToolResult.DONE` (`ToolStatus.DONE`) |
| `task_id` | `hcw-04-008-golden` |
| `correlation_id` | `corr-hcw-04-008-golden` |
| `diff_hash` | `cc1631c25d9fe07728b20012b719d4692ef775b99b3a6464f15d3a5d922c4e21` |
| `token_hash` | `f789d7fde3fa7a3283bae562890f99bf3b006ba29a5e370dd85d69024615ce72` |

O `ToolResult.DONE` é produzido pelo `SimpleRunner` depois de validar o token opaco
emitido pela UI local. O valor do token não é gravado: a ligação ao token é feita
pelo `token_hash` (SHA-256 do token), pelo `task_id` e pelo `diff_hash`. O mesmo
`correlation_id` atravessa o fluxo CREATE e o evento `execution.concluido`.

## Encadeamento verificável

1. `CreateWorkflow` executa os passos até `Step.APROVACAO` e pára sem token.
2. A UI local emite um token ligado a `task_id`, `correlation_id` e `diff_hash`.
3. `CreateWorkflow` valida o token e guarda apenas `hash_token(token)`.
4. `SimpleRunner` valida novamente tarefa, correlação, diff e prazo antes de criar o
   subprocesso.
5. O subprocesso grava `main.py` e `test_main.py` na pasta temporária autorizada e
   corre `pytest -q test_main.py`.
6. Com código de saída 0, o resultado é `ToolResult.DONE` com evidência de
   `workspace`, `returncode` e `stdout_sha256`.

## Ficheiros do caso dourado

- `tests/eval/fixtures/calculadora_cli/main.py`
- `tests/eval/fixtures/calculadora_cli/test_main.py`
- `tests/eval/fixtures/calculadora_cli/README.txt`
- `tests/integration/test_create_golden.py`

O subprocesso não lê a fixture do disco: o conteúdo é lido pelo processo de teste e
incorporado no comando Python, de forma determinística. Assim a guarda de ficheiros
do executor continua a limitar escritas e leituras à pasta autorizada.

## Limites e verificação

- Fornecedor de modelo é local e determinístico (`ProviderKind.FAKE`).
- O teste bloqueia `socket.getaddrinfo`, `socket.create_connection`,
  `socket.socket.connect` e `connect_ex` e falha se algum pedido externo for tentado.
- A guarda do subprocesso bloqueia rede e ficheiros fora da pasta autorizada.
- O executor é explicitamente não isolado (`isolated=False`); não é uma sandbox.
- A guarda passou a aceitar leitura da biblioteca do environment virtual e o dispositivo
  `os.devnull`, necessários para o `pytest` real; escritas fora da pasta autorizada
  continuam proibidas e a rede continua desactivada.
- O comando da fixture define `TEMP`, `TMP` e `TMPDIR` dentro da pasta autorizada para
  que o `pytest` não tente criar ficheiros no diretório temporário do sistema.

Resultado observado: `7 passed in 2.37s` nos testes focados (caso dourado e segurança do
executor). Resultado final e comandos completos: `reports/tasks/HCW-04-008-tests.txt`.
