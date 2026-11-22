"""Valores por omissão da configuração do HybridCrewAI."""

from __future__ import annotations

APP_NAME = "HybridCrewAI"
DATA_DIR = "data"
LOG_DIR = "logs"
EVENT_LOG = "logs/events.jsonl"
SQLITE_PATH = "data/hybridcrewai.sqlite3"
LOG_LEVEL = "INFO"
CLOUD_ENABLED = False
CLOUD_CONSENT_DEFAULT = False
GEMINI_ACCOUNT_TYPE_DEFAULT = "unknown"
MAX_FILE_LINES = 300
ENV_PREFIX = "HCW_"
ALLOWED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
