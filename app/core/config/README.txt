MÓDULO: core/config
FINALIDADE: Carregar uma configuração imutável e validada sem gravar ficheiros nem ler segredos.
FUNCIONALIDADES: valores por omissão seguros; leitura de variáveis HCW_*; validação de níveis, booleanos, inteiros e caminhos; recusa de travessia de directórios.
ESTRUTURA: defaults.py (constantes); schema.py (Settings e ConfigError); loader.py (leitura do ambiente); __init__.py (API pública).
INTERFACE PÚBLICA: Settings, ConfigError, load_settings.
DEPENDÊNCIAS: biblioteca padrão (dataclasses, os, pathlib, typing).
CONFIGURAÇÃO: HCW_APP_NAME, HCW_DATA_DIR, HCW_LOG_DIR, HCW_EVENT_LOG, HCW_SQLITE_PATH, HCW_LOG_LEVEL, HCW_CLOUD_ENABLED, HCW_MAX_FILE_LINES.
UTILIZAÇÃO: settings = load_settings(); print(settings.sqlite_path).
TESTES: python -m pytest -q tests/unit/test_config.py
LIMITAÇÕES: não lê ficheiros de configuração; segredos são tratados no módulo core/config/secrets na Fase 1.
RELAÇÕES: usado por core/logging, core/events, core/tasks, core/results e cli.
