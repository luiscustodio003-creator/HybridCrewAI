"""Contrato de resultados verificados de ferramentas."""

from app.core.results.statuses import ToolStatus
from app.core.results.tool_result import (
    ToolResult,
    ToolResultError,
    new_tool_result,
    validar_tool_result,
)

__all__ = [
    "ToolResult",
    "ToolResultError",
    "ToolStatus",
    "new_tool_result",
    "validar_tool_result",
]
