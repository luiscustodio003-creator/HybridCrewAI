"""Detecção e redacção de segredos antes de qualquer egress."""

from __future__ import annotations

import re
from collections.abc import Mapping

from app.core.logging import SecretRegistry

_REDACTED = "***REDACTED***"
_PADRAO_AWS = re.compile(r"AKIA[0-9A-Z]{16}")
_PADRAO_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_PADRAO_ATRIBUICAO = re.compile(
    r"(?i)\b([A-Za-z_][A-Za-z0-9_]*(?:key|token|secret|password)\s*[:=]\s*)([^\s,;]+)"
)


def redact_text(texto: str) -> str:
    """Substitui segredos conhecidos e padrões de chave por uma marca segura."""
    if not isinstance(texto, str):
        raise TypeError("texto tem de ser string.")
    resultado = SecretRegistry().redact(texto)
    resultado = _PADRAO_ATRIBUICAO.sub(rf"\1{_REDACTED}", resultado)
    resultado = _PADRAO_AWS.sub(_REDACTED, resultado)
    return _PADRAO_BEARER.sub(f"Bearer {_REDACTED}", resultado)


def contem_segredo(texto: str) -> bool:
    """Indica se o texto continha um segredo antes da redacção."""
    return redact_text(texto) != texto


def redact_mapping(valores: Mapping[str, str]) -> dict[str, str]:
    """Redige valores de cabeçalhos ou parâmetros sem alterar as chaves."""
    return {chave: redact_text(str(valor)) for chave, valor in valores.items()}
