"""Acesso à configuração da interface web local."""

from __future__ import annotations

from app.core.config import ConfigError, SecretStr, Settings


def ui_enabled(settings: Settings) -> bool:
    """Indica se a interface web local está habilitada."""
    return settings.ui_enabled


def require_ui_token(settings: Settings) -> SecretStr:
    """Devolve o token da interface sem o revelar em texto."""
    if settings.ui_token is None:
        raise ConfigError("HCW_UI_TOKEN não configurado; defina HCW_UI_TOKEN no ambiente.")
    if not settings.ui_enabled:
        raise ConfigError("HCW_UI_ENABLED tem de ser true para usar a interface web.")
    return settings.ui_token
