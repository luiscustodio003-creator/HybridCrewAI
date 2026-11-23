"""API pública da interface web local."""

from app.ui.config import require_ui_token, ui_enabled
from app.ui.server import create_server

__all__ = ["create_server", "require_ui_token", "ui_enabled"]
