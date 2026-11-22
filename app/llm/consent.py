"""Consentimento cloud persistido sem guardar credenciais."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from app.core.config.defaults import CLOUD_CONSENT_DEFAULT, GEMINI_ACCOUNT_TYPE_DEFAULT

_SQL_CRIAR = """
CREATE TABLE IF NOT EXISTS cloud_consent (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    account_type TEXT NOT NULL,
    granted INTEGER NOT NULL,
    updated_at TEXT NOT NULL
)
"""
_SQL_GUARDAR = """
INSERT INTO cloud_consent (singleton, account_type, granted, updated_at)
VALUES (1, ?, ?, ?)
ON CONFLICT(singleton) DO UPDATE SET
    account_type=excluded.account_type,
    granted=excluded.granted,
    updated_at=excluded.updated_at
"""


class AccountType(StrEnum):
    """Tipo de conta Gemini; desconhecido nunca autoriza cloud."""

    PERSONAL = "personal"
    WORK = "work"
    UNKNOWN = "unknown"


class ConsentError(ValueError):
    """Consentimento ou tipo de conta inválido."""


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    """Estado persistido do consentimento cloud."""

    account_type: AccountType
    granted: bool
    updated_at: str


class CloudConsentStore:
    """Armazena consentimento e tipo de conta em SQLite local."""

    __slots__ = ("_path",)

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Caminho do ficheiro SQLite."""
        return self._path

    def _connect(self) -> sqlite3.Connection:
        ligacao = sqlite3.connect(self._path, timeout=5)
        ligacao.row_factory = sqlite3.Row
        ligacao.execute("PRAGMA busy_timeout=5000")
        return ligacao

    def initialize(self) -> None:
        """Cria a pasta e a tabela, se necessário."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as ligacao:
            with ligacao:
                ligacao.execute(_SQL_CRIAR)

    @staticmethod
    def _agora() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")

    @staticmethod
    def _converter_tipo(valor: AccountType | str) -> AccountType:
        try:
            return AccountType(str(valor).strip().lower())
        except ValueError as erro:
            permitidos = ", ".join(item.value for item in AccountType)
            raise ConsentError(
                f"Tipo de conta inválido {valor!r}; use {permitidos}."
            ) from erro

    def get(self) -> ConsentRecord:
        """Devolve o registo actual ou o estado seguro por omissão."""
        self.initialize()
        with closing(self._connect()) as ligacao:
            linha = ligacao.execute(
                "SELECT account_type, granted, updated_at FROM cloud_consent WHERE singleton = 1"
            ).fetchone()
        if linha is None:
            return ConsentRecord(
                account_type=AccountType(GEMINI_ACCOUNT_TYPE_DEFAULT),
                granted=CLOUD_CONSENT_DEFAULT,
                updated_at="",
            )
        return ConsentRecord(
            account_type=AccountType(linha["account_type"]),
            granted=bool(linha["granted"]),
            updated_at=linha["updated_at"],
        )

    def _guardar(self, registo: ConsentRecord) -> ConsentRecord:
        with closing(self._connect()) as ligacao:
            with ligacao:
                ligacao.execute(
                    _SQL_GUARDAR,
                    (
                        registo.account_type.value,
                        int(registo.granted),
                        registo.updated_at,
                    ),
                )
        return registo

    def grant(self, account_type: AccountType | str) -> ConsentRecord:
        """Regista consentimento explícito; desconhecido continua negado."""
        self.initialize()
        tipo = self._converter_tipo(account_type)
        permitido = tipo is not AccountType.UNKNOWN
        return self._guardar(
            ConsentRecord(tipo, CLOUD_CONSENT_DEFAULT or permitido, self._agora())
        )

    def revoke(self) -> ConsentRecord:
        """Revoga o consentimento mantendo o tipo de conta."""
        atual = self.get()
        return self._guardar(
            ConsentRecord(atual.account_type, False, self._agora())
        )

    def allows_cloud(self) -> bool:
        """Indica se há consentimento válido para pedidos cloud."""
        registo = self.get()
        return registo.granted and registo.account_type is not AccountType.UNKNOWN
