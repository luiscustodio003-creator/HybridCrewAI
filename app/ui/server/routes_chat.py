"""Pedidos HTTP do chat persistido da interface web."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

CHAT_PATH = "/api/chat"
MAX_CORPO_BYTES = 8192
MAX_MENSAGEM_CHARS = 4000


def _texto_obrigatorio(valor: object, nome: str) -> str:
    """Valida e normaliza um campo textual obrigatório."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"O campo {nome} é obrigatório e não pode estar vazio.")
    return valor.strip()


def analisar_corpo(corpo: bytes) -> tuple[str, str, str]:
    """Valida o corpo JSON e extrai mensagem, tarefa e correlação."""
    if not isinstance(corpo, bytes) or not corpo:
        raise ValueError("O corpo do pedido é obrigatório.")
    if len(corpo) > MAX_CORPO_BYTES:
        raise ValueError("O corpo do pedido é demasiado grande.")
    try:
        dados = json.loads(corpo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ValueError("O corpo do pedido não é JSON válido.") from erro
    if not isinstance(dados, dict):
        raise ValueError("O corpo do pedido tem de ser um objecto JSON.")
    mensagem = _texto_obrigatorio(dados.get("message"), "message")
    if len(mensagem) > MAX_MENSAGEM_CHARS:
        raise ValueError("A mensagem é demasiado longa.")
    tarefa = _texto_obrigatorio(dados.get("task_id"), "task_id")
    correlacao = _texto_obrigatorio(dados.get("correlation_id"), "correlation_id")
    return mensagem, tarefa, correlacao


def analisar_filtro_tarefa(consulta: str) -> str | None:
    """Lê um único task_id não vazio da consulta."""
    parametros = parse_qs(consulta, keep_blank_values=True)
    valores = parametros.get("task_id")
    if not valores:
        return None
    if len(valores) != 1 or not valores[0].strip():
        raise ValueError("task_id tem de ter um valor não vazio.")
    return valores[0]
