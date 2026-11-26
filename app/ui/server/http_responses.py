"""Escrita de respostas HTTP locais com cabeçalhos de isolamento."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Final

TIPO_JSON: Final = "application/json; charset=utf-8"
POLITICA_SEGURANCA: Final = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
)

Payload = dict[str, object] | list[dict[str, object]]


def enviar_json(
    handler: BaseHTTPRequestHandler,
    status: HTTPStatus,
    payload: Payload,
) -> None:
    """Escreve uma resposta JSON curta e com tipo declarado."""
    corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", TIPO_JSON)
    handler.send_header("Content-Length", str(len(corpo)))
    handler.end_headers()
    handler.wfile.write(corpo)


def enviar_asset(handler: BaseHTTPRequestHandler, corpo: bytes, tipo: str) -> None:
    """Serve um recurso estático local com cabeçalhos de isolamento."""
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", tipo)
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.send_header("Content-Security-Policy", POLITICA_SEGURANCA)
    handler.end_headers()
    handler.wfile.write(corpo)


__all__ = ["enviar_asset", "enviar_json"]
