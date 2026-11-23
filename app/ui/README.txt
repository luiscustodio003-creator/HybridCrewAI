MÓDULO: ui
FINALIDADE: Expor a configuração da interface web local sem revelar o token nem iniciar servidores.
FUNCIONALIDADES: feature flag ui desligada por omissão; leitura do token a partir de HCW_UI_TOKEN; recusa de configuração sem token; representação redigida do segredo.
ESTRUTURA: config.py (ui_enabled, require_ui_token); __init__.py (API pública).
INTERFACE PÚBLICA: ui_enabled, require_ui_token.
DEPENDÊNCIAS: core/config; biblioteca padrão (typing).
CONFIGURAÇÃO: HCW_UI_ENABLED (false por omissão) e HCW_UI_TOKEN (sem valor por omissão; mínimo 16 caracteres).
UTILIZAÇÃO: if ui_enabled(settings): token = require_ui_token(settings).reveal().
TESTES: python -m pytest -q tests/unit/test_ui_config.py
LIMITAÇÕES: não inicia servidor, não abre browser e não escreve ficheiros; apenas valida e expõe a configuração da interface.
RELAÇÕES: prepara o servidor local previsto para HCW-03-003 e HCW-03-004.
