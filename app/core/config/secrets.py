"""Segredos em memória, sem gravação em ficheiros nem exposição em texto."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from typing import Protocol

DEFAULT_ALLOWED_SECRET_NAMES = ("GEMINI_API_KEY",)
_SECRET_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
_REDACTED = "***REDACTED***"


class SecretError(ValueError):
    """Nome de segredo inválido ou valor obrigatório ausente."""


class SecretStr:
    """Valor sensível cuja representação nunca revela o conteúdo."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        """Devolve o valor apenas quando o chamador o pede explicitamente."""
        return self._value

    def __str__(self) -> str:
        return _REDACTED

    def __repr__(self) -> str:
        return f"SecretStr({_REDACTED})"


class SecretProvider(Protocol):
    """Fonte de segredos injectada; não gravada em disco pelo módulo."""

    def get(self, name: str) -> str | None:
        """Devolve o valor de um nome ou None quando ausente."""
        ...


class EnvironmentSecrets:
    """Fornecedor que lê apenas variáveis de ambiente autorizadas."""

    __slots__ = ("_environ",)

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def get(self, name: str) -> str | None:
        """Lê uma variável de ambiente sem a gravar."""
        return self._environ.get(name)

    def __repr__(self) -> str:
        return "EnvironmentSecrets(<ambiente>)"


class Secrets:
    """Porta de entrada para segredos, com lista explícita de nomes permitidos."""

    __slots__ = ("_allowed", "_provider")

    def __init__(
        self,
        provider: SecretProvider,
        allowed_names: Iterable[str] = DEFAULT_ALLOWED_SECRET_NAMES,
    ) -> None:
        self._provider = provider
        self._allowed = frozenset(allowed_names)

    def _validate_name(self, name: str) -> None:
        """Aceita apenas nomes declarados e em maiúsculas."""
        if not _SECRET_NAME.fullmatch(name):
            raise SecretError(f"Nome de segredo inválido: {name!r}.")
        if name not in self._allowed:
            raise SecretError(f"Segredo {name} não está declarado nesta aplicação.")

    def get(self, name: str) -> SecretStr | None:
        """Devolve o segredo ou None; nunca escreve ficheiros."""
        self._validate_name(name)
        value = self._provider.get(name)
        if value is None or not value.strip():
            return None
        return SecretStr(value)

    def require(self, name: str) -> SecretStr:
        """Exige um segredo configurado, falhando com mensagem sem valor."""
        secret = self.get(name)
        if secret is None:
            raise SecretError(f"Segredo {name} não configurado; defina {name} no ambiente.")
        return secret

    def __repr__(self) -> str:
        names = sorted(self._allowed)
        return f"Secrets(names={names})"


def redact(text: str, secrets: Iterable[SecretStr]) -> str:
    """Substitui valores sensíveis por uma marca antes de escrever logs."""
    result = text
    for secret in secrets:
        value = secret.reveal()
        if value:
            result = result.replace(value, _REDACTED)
    return result
