"""Delimitação de conteúdo não confiável para prompts."""

from __future__ import annotations

INICIO = "<<<CONTEUDO_NAO_CONFIAVEL>>>"
FIM = "<<<FIM_CONTEUDO_NAO_CONFIAVEL>>>"


class UntrustedContentError(ValueError):
    """Conteúdo tenta forjar os marcadores de confiança."""


def wrap_untrusted(texto: str) -> str:
    """Devolve o texto dentro de marcadores que o marcam como dado."""
    if not isinstance(texto, str):
        raise TypeError("texto tem de ser string.")
    if INICIO in texto or FIM in texto:
        raise UntrustedContentError("Marcadores de conteúdo não confiável são proibidos.")
    return f"{INICIO}\n{texto}\n{FIM}"
