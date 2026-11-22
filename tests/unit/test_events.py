"""Testes do modelo de eventos, do barramento e do escritor JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.events import (
    EventBus,
    EventBusError,
    EventContext,
    EventLevel,
    EventValidationError,
    JsonlSink,
    new_event,
    read_events,
)

if TYPE_CHECKING:
    from app.core.events import Event

EVENT_COUNT = 3
CONTEXTO = EventContext(
    correlation_id="corr-1",
    task_id="HCW-01-004",
    agent="open-code",
    phase="1",
)
CAMPOS_CONTEXT = ("correlation_id", "task_id", "agent", "phase")
REQUIRED_KEYS = {
    "event_id",
    "occurred_at",
    "correlation_id",
    "task_id",
    "agent",
    "phase",
    "level",
    "kind",
    "message",
    "data",
}


class CollectingSink:
    """Sink em memória para observar entregas."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def write(self, event: Event) -> None:
        """Guarda o evento recebido."""
        self.events.append(event)


class FailingSink:
    """Sink que falha de propósito para testar resiliência."""

    def write(self, event: Event) -> None:
        """Falha sem tocar no evento."""
        raise RuntimeError("falha de teste")


def criar_evento(kind: str = "task.started") -> Event:
    """Cria um evento com todos os campos obrigatórios."""
    return new_event(CONTEXTO, kind=kind, message="Evento de teste")


def test_evento_tem_campos_obrigatorios() -> None:
    event = criar_evento()
    payload = event.to_dict()
    assert REQUIRED_KEYS.issubset(payload)
    assert payload["level"] == EventLevel.INFO.value
    assert payload["correlation_id"] == "corr-1"


@pytest.mark.parametrize("campo", [*CAMPOS_CONTEXT, "kind"])
def test_campos_obrigatorios_vazios_sao_recusados(campo: str) -> None:
    valores = {
        "correlation_id": "corr-1",
        "task_id": "HCW-01-004",
        "agent": "open-code",
        "phase": "1",
        "kind": "task.started",
    }
    valores[campo] = "  "
    if campo == "kind":
        with pytest.raises(EventValidationError, match=campo):
            new_event(CONTEXTO, kind=valores["kind"], message="Evento")
    else:
        contexto_invalido = {nome: valores[nome] for nome in CAMPOS_CONTEXT}
        with pytest.raises(EventValidationError, match=campo):
            EventContext(**contexto_invalido)


def test_event_id_unico_e_timestamp_utc() -> None:
    primeiro = criar_evento()
    segundo = criar_evento()
    assert primeiro.event_id != segundo.event_id
    assert primeiro.occurred_at.endswith("+00:00")


def test_bus_entrega_a_todos_os_sinks() -> None:
    primeiro = CollectingSink()
    segundo = CollectingSink()
    bus = EventBus([primeiro, segundo])
    event = criar_evento()
    bus.publish(event)
    assert primeiro.events == [event]
    assert segundo.events == [event]


def test_bus_notifica_mesmo_se_um_sink_falha() -> None:
    bom = CollectingSink()
    bus = EventBus([FailingSink(), bom])
    event = criar_evento()
    with pytest.raises(EventBusError):
        bus.publish(event)
    assert bom.events == [event]


def test_jsonl_uma_linha_por_evento_e_valida(tmp_path: Path) -> None:
    caminho = tmp_path / "events.jsonl"
    bus = EventBus([JsonlSink(caminho)])
    criados = [criar_evento(f"task.passo.{indice}") for indice in range(EVENT_COUNT)]
    for event in criados:
        bus.publish(event)

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert len(linhas) == EVENT_COUNT
    for linha in linhas:
        assert REQUIRED_KEYS.issubset(json.loads(linha))
    lidos = read_events(caminho)
    assert [event.event_id for event in lidos] == [event.event_id for event in criados]


def test_jsonl_rejeita_valor_nao_serializavel(tmp_path: Path) -> None:
    caminho = tmp_path / "events.jsonl"
    event = new_event(
        CONTEXTO,
        kind="task.started",
        message="Evento",
        data={"objeto": object()},
    )
    with pytest.raises(TypeError):
        JsonlSink(caminho).write(event)
