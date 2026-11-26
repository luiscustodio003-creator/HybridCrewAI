MÓDULO: core/local_auth
FINALIDADE: Centralizar a verificação local de origem e de cabeçalhos Bearer sem depender do servidor da interface web.
FUNCIONALIDADES: aceitar apenas esquema http e anfitrião 127.0.0.1 ou localhost; gerar a origem exacta a partir da porta; validar Origin e Sec-Fetch-Site; exigir Authorization: Bearer nas rotas protegidas; devolver falsos em vez de lançar excepções.
ESTRUTURA: local_auth.py (constantes e funções de validação); __init__.py (marcador do pacote).
INTERFACE PÚBLICA: BEARER, LOCAL_HOST, LOCAL_SCHEME, origin_local, origem_valida, pedido_autorizado.
DEPENDÊNCIAS: biblioteca padrão (hmac, typing, urllib.parse).
CONFIGURAÇÃO: sem variáveis de ambiente próprias; a porta é sempre fornecida pelo chamador.
UTILIZAÇÃO: if not pedido_autorizado(cabecalhos, porta): recusar(); origem_valida(cabecalhos, porta) para aceitar apenas pedidos locais.
TESTES: python -m pytest -q tests/security/test_ui_local.py tests/security/test_approval_tokens.py tests/integration/test_ui_approvals.py tests/unit/test_ui_web_assets.py
LIMITAÇÕES: não emite tokens, não lê configuração e não substitui a validação de corpo das rotas; endereços IPv6 e domínios personalizados não são aceites.
RELAÇÕES: usado por approvals/tokens e ui/server; depende apenas da biblioteca padrão.
