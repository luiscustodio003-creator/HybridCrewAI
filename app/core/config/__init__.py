"""API pública do módulo de configuração."""

from app.core.config.loader import load_settings
from app.core.config.schema import ConfigError, Settings

__all__ = ["ConfigError", "Settings", "load_settings"]
