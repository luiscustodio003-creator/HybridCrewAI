"""Recursos estáticos locais do cliente web."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

ASSETS_DIR: Final = Path(__file__).resolve().parents[1] / "web"
WEB_FILES: Final[Mapping[str, tuple[str, str]]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/tasks.js": ("tasks.js", "text/javascript; charset=utf-8"),
    "/logs.js": ("logs.js", "text/javascript; charset=utf-8"),
    "/llm_calls.js": ("llm_calls.js", "text/javascript; charset=utf-8"),
    "/chat.js": ("chat.js", "text/javascript; charset=utf-8"),
    "/agents.js": ("agents.js", "text/javascript; charset=utf-8"),
    "/approvals.js": ("approvals.js", "text/javascript; charset=utf-8"),
}


def ler_asset(caminho: str) -> tuple[bytes, str] | None:
    """Devolve os bytes e o tipo MIME de um recurso local conhecido."""
    entrada = WEB_FILES.get(caminho)
    if entrada is None:
        return None
    nome, tipo = entrada
    return (ASSETS_DIR / nome).read_bytes(), tipo
