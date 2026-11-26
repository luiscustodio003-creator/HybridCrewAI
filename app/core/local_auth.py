"""Autenticação e validação de origem do servidor local."""

from __future__ import annotations

from collections.abc import Mapping
from hmac import compare_digest

from app.core.config import Settings

BEARER = "Bearer"
LOCAL_HOST = "127.0.0.1"
LOCAL_SCHEME = "http"


def origin_local(porta: int) -> str:
    """Devolve a única origem aceite pelo servidor local."""
    return f"{LOCAL_SCHEME}://{LOCAL_HOST}:{porta}"


def origem_valida(
    origem: str | None,
    porta: int,
    sec_fetch_site: str | None = None,
) -> bool:
    """Aceita a origem exata ou pedidos de mesma origem do browser."""
    if origem is not None:
        return compare_digest(
            origem.encode("utf-8"), origin_local(porta).encode("utf-8")
        )
    return sec_fetch_site == "same-origin"


def pedido_autorizado(cabecalhos: Mapping[str, str], settings: Settings) -> bool:
    """Valida o esquema Bearer contra o token em segredo, sem o divulgar."""
    if not settings.ui_enabled or settings.ui_token is None:
        return False
    autorizacao = cabecalhos.get("Authorization", "").strip()
    esquema, separador, valor = autorizacao.partition(" ")
    if separador != " " or esquema.lower() != BEARER.lower() or not valor:
        return False
    esperado = settings.ui_token.reveal().encode("utf-8")
    return compare_digest(valor.strip().encode("utf-8"), esperado)
