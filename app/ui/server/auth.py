"""Reexportação da autenticação local para a API do servidor web."""

from app.core.local_auth import (
    BEARER,
    LOCAL_HOST,
    LOCAL_SCHEME,
    origem_valida,
    origin_local,
    pedido_autorizado,
)

__all__ = [
    "BEARER",
    "LOCAL_HOST",
    "LOCAL_SCHEME",
    "origin_local",
    "origem_valida",
    "pedido_autorizado",
]
