# Tokens de aprovação da interface local

## Objectivo

Emitir um token opaco apenas quando o pedido chega do servidor local autenticado da interface web e validar esse token contra a tarefa, o hash do diff e um prazo de 15 minutos.

Uma saída de modelo com `approved=true` não emite token: o runner apenas regista `approval_claim` e não tem acesso a `TokenStore.emitir` com cabeçalhos válidos da interface.

## API pública

- `SolicitacaoAprovacao`: pedido com `task_id`, `correlation_id`, `diff_hash`, cabeçalhos e porta local.
- `TokenStore.emitir`: emite `ApprovalToken` após validar Bearer e `Origin` da interface.
- `TokenStore.validar`: valida token, tarefa, hash do diff e expiração.
- `ApprovalToken`: valor opaco e metadados; o valor do token está oculto em `repr`.
- Excepções tipadas: `ApprovalDenied`, `DadosInvalidos`, `TokenInvalido`, `TokenExpirado`, `TarefaInvalida`, `DiffAlterado`.

## Regras

- Sem segredo em ficheiros, logs ou mensagens de erro: o valor em claro não é gravado.
- O hash do diff tem de ser SHA-256 hexadecimal com 64 caracteres.
- Tokens expiram 15 minutos após a emissão.
- O relógio é injectável para testes determinísticos.
- Nenhum token é emitido se a interface estiver desligada, sem Bearer válido ou com `Origin` externo.

## Testes

- `tests/unit/test_approval_tokens.py`
- `tests/security/test_approval_tokens.py`
