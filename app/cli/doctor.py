"""Verificações reais de configuração, SQLite e redacção da CLI."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from app.core.config import ConfigError, SecretStr, Settings, load_settings
from app.core.logging import SecretRegistry
from app.core.tasks import SqliteTaskStore

MARCA_REDACAO = "***REDACTED***"
CHAVE_FALSA = "sk-hcw-doctor-check"
NOME_FALSO = "DOCTOR_SECRET"
VALOR_FALSO = "abc123"


class DoctorError(RuntimeError):
    """Falha numa verificação de saúde da instalação."""


def verificar_config(base_dir: Path | None = None) -> Settings:
    """Carrega e valida a configuração sem gravar ficheiros."""
    return load_settings(None, base_dir)


def verificar_sqlite(settings: Settings) -> None:
    """Confirma que o esquema de tarefas pode ser criado e lido."""
    loja = SqliteTaskStore(settings.sqlite_path)
    loja.initialize()
    loja.list_tasks()


def verificar_redaccao() -> None:
    """Ataca a redacção com valores falsos e exige que não reapareçam."""
    registo = SecretRegistry(
        secrets=[SecretStr(CHAVE_FALSA)],
        names=[NOME_FALSO],
    )
    texto = registo.redact(f"token={CHAVE_FALSA} {NOME_FALSO}={VALOR_FALSO}")
    if CHAVE_FALSA in texto or VALOR_FALSO in texto or MARCA_REDACAO not in texto:
        raise DoctorError("A redacção não removeu valores sensíveis de teste.")


def run(base_dir: Path | None = None) -> int:
    """Executa as três verificações e devolve o código de saída da CLI."""
    try:
        settings = verificar_config(base_dir)
        print("config OK")
        verificar_sqlite(settings)
        print("sqlite OK")
        verificar_redaccao()
        print("redaction OK")
    except (ConfigError, DoctorError, OSError, sqlite3.Error, ValueError) as erro:
        print(f"doctor FAIL: {erro}", file=sys.stderr)
        return 1
    return 0
