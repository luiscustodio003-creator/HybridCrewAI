"""Esquema leve e verificável para resultados de ferramentas."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.results.statuses import ToolStatus


class ToolResultError(ValueError):
    """Violação do contrato de resultado de ferramenta."""


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Resultado imutável com estado verificável."""

    status: ToolStatus
    summary: str
    evidence: tuple[str, ...] = ()
    error: str | None = None
    question: str | None = None

    def __post_init__(self) -> None:
        """Rejeita resultados que não cumprem o esquema."""
        validar_tool_result(self)


_REQUERIDOS: dict[ToolStatus, tuple[tuple[str, str], ...]] = {
    ToolStatus.DONE: (("evidence", "evidencia"),),
    ToolStatus.FAILED: (("error", "error"),),
    ToolStatus.ASK: (("question", "question"),),
}
_PROIBIDOS: dict[ToolStatus, tuple[tuple[str, str], ...]] = {
    ToolStatus.DONE: (("error", "error"), ("question", "question")),
    ToolStatus.UNVERIFIED: (("error", "error"), ("question", "question")),
    ToolStatus.FAILED: (("question", "question"),),
    ToolStatus.ASK: (("error", "error"),),
    ToolStatus.STARTED: (
        ("error", "error"),
        ("question", "question"),
        ("evidence", "evidencia"),
    ),
}


def validar_tool_result(resultado: ToolResult) -> None:
    """Valida o esquema sem dependências externas."""
    if not isinstance(resultado.status, ToolStatus):
        raise ToolResultError("estado invalido")
    if not resultado.summary.strip():
        raise ToolResultError("summary e obrigatorio")
    for item in resultado.evidence:
        if not item.strip():
            raise ToolResultError("evidencia nao pode ser vazia")

    estado = resultado.status.value
    for campo, rotulo in _REQUERIDOS.get(resultado.status, ()):
        if not getattr(resultado, campo):
            raise ToolResultError(f"{estado} requer {rotulo}")
    for campo, rotulo in _PROIBIDOS.get(resultado.status, ()):
        if getattr(resultado, campo):
            raise ToolResultError(f"{estado} nao aceita {rotulo}")


def new_tool_result(
    status: ToolStatus | str,
    summary: str,
    evidence: tuple[str, ...] | list[str] = (),
    error: str | None = None,
    question: str | None = None,
) -> ToolResult:
    """Constrói um resultado normalizando a evidência."""
    estado = status if isinstance(status, ToolStatus) else ToolStatus(status)
    return ToolResult(
        status=estado,
        summary=summary,
        evidence=tuple(evidence),
        error=error,
        question=question,
    )
