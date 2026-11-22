"""Seguimento de eventos JSONL para a interface de linha de comando."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import monotonic, sleep
from typing import TextIO

from app.core.events import Event, EventValidationError

INTERVALO_SEGUNDOS = 0.1


def formatar_evento(evento: Event) -> str:
    """Formata um evento com todos os campos de rastreabilidade."""
    return (
        f"[{evento.occurred_at}] {evento.level.name} {evento.phase} "
        f"{evento.correlation_id} {evento.task_id} {evento.agent} "
        f"{evento.kind}: {evento.message}"
    )


def _interpretar_linha(linha: str) -> Event | None:
    """Ignora linhas corrompidas sem interromper o seguimento."""
    try:
        return Event.from_dict(json.loads(linha))
    except (json.JSONDecodeError, EventValidationError, TypeError):
        return None


def follow(
    path: Path,
    *,
    task_id: str | None = None,
    limit: int = 1,
    timeout: float = 10.0,
    stream: TextIO | None = None,
) -> int:
    """Segue novos eventos e devolve zero quando mostra pelo menos um."""
    if limit < 1:
        raise ValueError("limit tem de ser maior que zero.")
    destino = sys.stdout if stream is None else stream
    posicao = path.stat().st_size if path.exists() else 0
    vistos = 0
    inicio = monotonic()

    while vistos < limit and monotonic() - inicio < timeout:
        if path.exists():
            with path.open("rb") as ficheiro:
                ficheiro.seek(posicao)
                while True:
                    linha = ficheiro.readline()
                    if not linha:
                        break
                    posicao += len(linha)
                    evento = _interpretar_linha(linha.decode("utf-8", errors="replace"))
                    if evento is None:
                        continue
                    if task_id is not None and evento.task_id != task_id:
                        continue
                    destino.write(formatar_evento(evento) + "\n")
                    destino.flush()
                    vistos += 1
                    if vistos >= limit:
                        break
        if vistos < limit:
            sleep(INTERVALO_SEGUNDOS)

    return 0 if vistos else 2
