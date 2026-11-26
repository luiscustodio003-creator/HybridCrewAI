"""Rotas de equipa e aprovação da interface local."""

from __future__ import annotations

import json
from collections.abc import Mapping
from http import HTTPStatus
from typing import Final

from agents.definitions import DefinitionError, load_agent_definitions
from approvals.tokens import (
    ApprovalDenied,
    DadosInvalidos,
    SolicitacaoAprovacao,
    TokenStore,
    hash_diff_obrigatorio,
    texto_obrigatorio,
)

AGENTS_PATH: Final = "/api/agents"
APPROVALS_PATH: Final = "/api/approvals"
CAMPOS_APROVACAO: Final = frozenset({"task_id", "correlation_id", "diff_hash"})


def listar_agentes() -> list[dict[str, object]]:
    """Devolve metadados públicos da equipa, sem prompts nem instruções."""
    try:
        definicoes = load_agent_definitions()
    except DefinitionError as exc:
        raise DadosInvalidos(str(exc)) from exc
    return [
        {
            "agent_id": definicao.agent_id,
            "nome": definicao.nome,
            "versao": definicao.versao,
            "entrada": definicao.entrada,
            "saida": definicao.saida,
            "ferramentas": list(definicao.ferramentas),
        }
        for definicao in definicoes
    ]


def analisar_aprovacao(corpo: bytes) -> tuple[str, str, str]:
    """Valida o corpo JSON e devolve os três campos obrigatórios."""
    try:
        dados = json.loads(corpo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DadosInvalidos("Corpo JSON inválido.") from exc
    if not isinstance(dados, dict) or set(dados) != CAMPOS_APROVACAO:
        raise DadosInvalidos(
            "O corpo tem de conter apenas task_id, correlation_id e diff_hash."
        )
    tarefa = texto_obrigatorio(dados["task_id"], "task_id")
    correlacao = texto_obrigatorio(dados["correlation_id"], "correlation_id")
    diff = hash_diff_obrigatorio(dados["diff_hash"])
    return tarefa, correlacao, diff


def emitir_aprovacao(
    tokens: TokenStore,
    porta: int,
    cabecalhos: Mapping[str, str],
    corpo: bytes,
) -> dict[str, object]:
    """Emite um token opaco ligado à tarefa, correlação e diff validados."""
    tarefa, correlacao, diff = analisar_aprovacao(corpo)
    solicitacao = SolicitacaoAprovacao(
        task_id=tarefa,
        correlation_id=correlacao,
        diff_hash=diff,
        headers=cabecalhos,
        porta=porta,
    )
    registro = tokens.emitir(solicitacao)
    return {
        "task_id": registro.task_id,
        "correlation_id": registro.correlation_id,
        "diff_hash": registro.diff_hash,
        "emitida_em": registro.emitido_em.isoformat(),
        "expira_em": registro.expira_em.isoformat(),
        "token": registro.token,
    }


Payload = dict[str, object] | list[dict[str, object]]


def resposta_agentes() -> tuple[HTTPStatus, Payload]:
    """Prepara a resposta da equipa, sem expor prompts nem instruções."""
    try:
        return HTTPStatus.OK, listar_agentes()
    except DadosInvalidos as exc:
        return HTTPStatus.INTERNAL_SERVER_ERROR, {"error": {"message": str(exc)}}


def resposta_aprovacao(
    tokens: TokenStore,
    porta: int,
    cabecalhos: Mapping[str, str],
    corpo: bytes,
    limite: int,
) -> tuple[HTTPStatus, Payload]:
    """Prepara a resposta da emissão de token com erros tipados."""
    try:
        if not 0 < len(corpo) <= limite:
            raise ValueError("O corpo do pedido é obrigatório e está limitado.")
        registro = emitir_aprovacao(tokens, porta, cabecalhos, corpo)
    except (ValueError, DadosInvalidos) as exc:
        return HTTPStatus.BAD_REQUEST, {"error": {"message": str(exc)}}
    except ApprovalDenied as exc:
        return HTTPStatus.FORBIDDEN, {"error": {"message": str(exc)}}
    return HTTPStatus.OK, registro


__all__ = [
    "AGENTS_PATH",
    "APPROVALS_PATH",
    "analisar_aprovacao",
    "emitir_aprovacao",
    "listar_agentes",
    "resposta_agentes",
    "resposta_aprovacao",
]
