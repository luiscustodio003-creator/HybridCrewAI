MÓDULO: core/config
FINALIDADE: Carregar uma configuração imutável e validada e expor segredos sem os gravar nem revelar.
FUNCIONALIDADES: valores por omissão seguros; leitura de variáveis HCW_*; validação de níveis, booleanos, inteiros, caminhos, do nome do modelo Ollama e do token da interface; segredos em memória com representação redigida; redacção de texto para logs.
ESTRUTURA: defaults.py (constantes); schema.py (Settings, ConfigError e validação partilhada); loader.py (leitura do ambiente); secrets.py (Secrets, SecretStr, EnvironmentSecrets e redact); __init__.py (API pública).
INTERFACE PÚBLICA: Settings, ConfigError, load_settings, validate_ollama_model, validate_ui_token, Secrets, SecretStr, EnvironmentSecrets, SecretError, redact.
DEPENDÊNCIAS: biblioteca padrão (dataclasses, os, pathlib, re, typing).
CONFIGURAÇÃO: HCW_APP_NAME, HCW_DATA_DIR, HCW_LOG_DIR, HCW_EVENT_LOG, HCW_SQLITE_PATH, HCW_LOG_LEVEL, HCW_CLOUD_ENABLED, HCW_MAX_FILE_LINES, HCW_OLLAMA_MODEL (sem valor por omissão), HCW_UI_ENABLED (false por omissão), HCW_UI_TOKEN (sem valor por omissão; mínimo 16 caracteres) e HCW_CREATE_FLOW (false por omissão). Nomes de segredos permitidos por omissão: GEMINI_API_KEY (nome apenas; nunca um valor).
UTILIZAÇÃO: settings = load_settings(); modelo = settings.ollama_model; criar = settings.create_flow; store = Secrets(EnvironmentSecrets()); chave = store.require("GEMINI_API_KEY").reveal().
TESTES: python -m pytest -q tests/unit/test_config.py tests/unit/test_ui_config.py tests/unit/test_create_flow_config.py tests/security/test_secrets.py
LIMITAÇÕES: não lê ficheiros de configuração nem keyring; não carrega endereços de fornecedores; não envia segredos para a cloud; um modelo Ollama ausente ou vazio aborta com ConfigError, sem nome inventado; a flag HCW_CREATE_FLOW apenas habilita o fluxo, não executa nada por si.
RELAÇÕES: usado por core/logging, core/events, core/tasks, core/results, llm/providers e cli.
