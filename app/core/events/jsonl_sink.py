"""Persistência de eventos em ficheiro JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from app.core.events.models import Event


class JsonlSink:
    """Escreve um evento por linha, de forma atómica por instância."""

    __slots__ = ("_lock", "_path")

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()

    @property
    def path(self) -> Path:
        """Caminho do ficheiro de eventos."""
        return self._path

    def write(self, event: Event) -> None:
        """Acrescenta uma linha JSON válida e independente."""
        linha = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as ficheiro:
                ficheiro.write(f"{linha}\n")


def read_events(path: Path) -> list[Event]:
    """Lê todas as linhas válidas de um ficheiro JSONL."""
    if not path.exists():
        return []
    eventos: list[Event] = []
    with path.open("r", encoding="utf-8") as ficheiro:
        for linha in ficheiro:
            if linha.strip():
                eventos.append(Event.from_dict(json.loads(linha)))
    return eventos
