"""Identificadores determinísticos e estáveis para tarefas."""

from __future__ import annotations

import uuid

_ESPACO = uuid.NAMESPACE_URL
_PREFIXO = "hcw:task:"


def generate_task_id(chave: str) -> str:
    """Gera um UUIDv5 estável a partir de uma chave textual."""
    valor = chave.strip()
    if not valor:
        raise ValueError("A chave da tarefa é obrigatória.")
    return str(uuid.uuid5(_ESPACO, f"{_PREFIXO}{valor}"))
