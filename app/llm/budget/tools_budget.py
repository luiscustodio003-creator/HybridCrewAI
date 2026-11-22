"""Selecção curta e determinística de ferramentas para Ollama."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config.defaults import DEFAULT_MAX_TOOL_DESCRIPTION_CHARS


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Ferramenta com descrição breve e segura para o modelo."""

    name: str
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name de ferramenta inválido.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description de ferramenta inválida.")


def select_tools(
    ferramentas: list[ToolSpec] | tuple[ToolSpec, ...],
    max_tools: int,
    max_description_chars: int = DEFAULT_MAX_TOOL_DESCRIPTION_CHARS,
) -> list[ToolSpec]:
    """Devolve no máximo `max_tools`, com descrições truncadas."""
    if isinstance(max_tools, bool) or not isinstance(max_tools, int) or max_tools < 0:
        raise ValueError("max_tools tem de ser inteiro não negativo.")
    if (
        isinstance(max_description_chars, bool)
        or not isinstance(max_description_chars, int)
        or max_description_chars < 1
    ):
        raise ValueError("max_description_chars tem de ser inteiro positivo.")
    if max_tools == 0:
        return []
    selecionadas: list[ToolSpec] = []
    for ferramenta in sorted(ferramentas, key=lambda item: item.name)[:max_tools]:
        resumo = " ".join(ferramenta.description.split())
        if len(resumo) > max_description_chars:
            resumo = resumo[: max_description_chars - 1] + "…"
        selecionadas.append(ToolSpec(ferramenta.name, resumo))
    return selecionadas
