"""Estados verificáveis dos resultados de ferramentas."""

from __future__ import annotations

from enum import StrEnum


class ToolStatus(StrEnum):
    """Estado verificável devolvido por uma ferramenta."""

    DONE = "done"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    ASK = "ask"
    STARTED = "started"
