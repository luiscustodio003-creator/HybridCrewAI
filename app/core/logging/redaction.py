"""Registo de segredos e padrões a redigir antes de qualquer escrita de log."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.core.config import SecretStr, redact

_REDACTED = "***REDACTED***"
_PADRAO_CHAVE_API = re.compile(r"sk-[A-Za-z0-9_-]+")
_PADRAO_NOME_SECRETO = re.compile(r"[A-Z][A-Z0-9_]*")


class SecretRegistry:
    """Valores e nomes sensíveis conhecidos pelo processo."""

    __slots__ = ("_nomes", "_segredos")

    def __init__(
        self,
        secrets: Iterable[SecretStr] = (),
        names: Iterable[str] = (),
    ) -> None:
        self._segredos = list(secrets)
        self._nomes: list[str] = []
        for nome in names:
            self.register_name(nome)

    def register(self, secret: SecretStr) -> None:
        """Regista um valor sensível adicional."""
        self._segredos.append(secret)

    def register_name(self, name: str) -> None:
        """Regista um nome de variável cujo valor deve ser sempre redigido."""
        if not _PADRAO_NOME_SECRETO.fullmatch(name):
            raise ValueError(f"Nome de segredo inválido: {name!r}.")
        if name not in self._nomes:
            self._nomes.append(name)

    def redact(self, text: str) -> str:
        """Substitui valores sensíveis por uma marca segura."""
        resultado = redact(text, self._segredos)
        resultado = _PADRAO_CHAVE_API.sub(_REDACTED, resultado)
        for nome in self._nomes:
            padrao = re.compile(
                rf"(?i)\b({re.escape(nome)}\s*[:=]\s*)([^\s,;]+)"
            )
            resultado = padrao.sub(rf"\1{_REDACTED}", resultado)
        return resultado
