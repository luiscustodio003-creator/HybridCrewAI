"""API pública do módulo de configuração."""

from app.core.config.loader import load_settings
from app.core.config.schema import ConfigError, Settings
from app.core.config.secrets import (
    EnvironmentSecrets,
    SecretError,
    Secrets,
    SecretStr,
    redact,
)

__all__ = [
    "ConfigError",
    "EnvironmentSecrets",
    "SecretError",
    "SecretStr",
    "Secrets",
    "Settings",
    "load_settings",
    "redact",
]
