"""Carga determinística das definições usadas pelo runner."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from agents.definitions import AgentDefinition, DefinitionError, load_agent_definitions
from agents.runner.models import AgentRunError


class DefinitionNotFoundError(AgentRunError):
    """Identificador de agente sem definição local."""


def load_runner_definitions(
    base_dir: str | Path | None = None,
) -> dict[str, AgentDefinition]:
    """Devolve as definições locais indexadas por identificador."""
    try:
        definicoes = load_agent_definitions(base_dir)
    except DefinitionError as erro:
        raise AgentRunError(str(erro)) from erro
    return {definicao.agent_id: definicao for definicao in definicoes}


def obter_definicao(
    definicoes: Mapping[str, AgentDefinition],
    agent_id: str,
) -> AgentDefinition:
    """Obtém uma definição sem a interpretar como código."""
    if not isinstance(definicoes, Mapping):
        raise TypeError("definicoes tem de ser um mapping.")
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise AgentRunError("agent_id tem de ser texto não vazio.")
    definicao = definicoes.get(agent_id)
    if definicao is None:
        raise DefinitionNotFoundError(f"Agente desconhecido: {agent_id}.")
    return definicao
