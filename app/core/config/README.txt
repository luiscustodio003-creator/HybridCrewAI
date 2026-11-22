MÓDULO: core/config
FINALIDADE: Carregar uma configuração imutável e validada e expor segredos sem os gravar nem revelar.
FUNCIONALIDADES: valores por omissão seguros; leitura de variáveis HCW_*; validação de níveis, booleanos, inteiros e caminhos; segredos em memória com representação redigida; redacção de texto para logs.
ESTRUTURA: defaults.py (constantes); schema.py (Settings e ConfigError); loader.py (leitura do ambiente); secrets.py (Secrets, SecretStr, EnvironmentSecrets e redact); __init__.py (API pública).
INTERFACE PÚBLICA: Settings, ConfigError, load_settings, Secrets, SecretStr, EnvironmentSecrets, SecretError, redact.
DEPENDÊNCIAS: biblioteca padrão (dataclasses, os, pathlib, re, typing).
CONFIGURAÇÃO: HCW_APP_NAME, HCW_DATA_DIR, HCW_LOG_DIR, HCW_EVENT_LOG, HCW_SQLITE_PATH, HCW_LOG_LEVEL, HCW_CLOUD_ENABLED, HCW_MAX_FILE_LINES. Nomes de segredos permitidos por omissão: GEMINI_API_KEY (nome apenas; nunca um valor).
UTILIZAÇÃO: settings = load_settings(); store = Secrets(EnvironmentSecrets()); chave = store.require("GEMINI_API_KEY").reveal().
TESTES: python -m pytest -q tests/unit/test_config.py tests/security/test_secrets.py
LIMITAÇÕES: não lê ficheiros de configuração nem keyring; não envia segredos para a cloud; a redacção de logs será ligada em core/logging na Fase 1.
RELAÇÕES: usado por core/logging, core/events, core/tasks, core/results e cli.
