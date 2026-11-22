"""Utilitário de tempo em UTC para tarefas."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Devolve a hora actual em UTC com fuso horário."""
    return datetime.now(UTC)
