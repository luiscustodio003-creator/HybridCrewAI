"""Renderização segura de prompts a partir de definições de agentes."""

from __future__ import annotations

from collections.abc import Mapping

from agents.definitions.parser import AgentDefinition
from app.llm.egress import wrap_untrusted


def render_prompt(
    definicao: AgentDefinition,
    untrusted: Mapping[str, str] | None = None,
) -> str:
    """Junta blocos não confiáveis apenas através do delimitador seguro."""
    if not isinstance(definicao, AgentDefinition):
        raise TypeError("definicao tem de ser AgentDefinition.")
    if untrusted is None:
        return definicao.texto
    if not isinstance(untrusted, Mapping):
        raise TypeError("untrusted tem de ser um mapping.")
    partes = [definicao.texto]
    for nome, conteudo in untrusted.items():
        if not isinstance(nome, str) or not isinstance(conteudo, str):
            raise TypeError("Chaves e valores de untrusted têm de ser strings.")
        partes.append(f"{nome}:\n{wrap_untrusted(conteudo)}")
    return "\n\n".join(partes)
