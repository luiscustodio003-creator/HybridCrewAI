"""Stream SSE de eventos com filtros e latência real."""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from http import HTTPStatus
from http.client import HTTPConnection, HTTPResponse
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import load_settings
from app.core.events import EventContext, EventLevel, JsonlSink, new_event
from app.ui.server import create_server
from app.ui.server.app import UiServer
from app.ui.server.routes_events import EVENTS_PATH

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
CONTEXTO = EventContext(
    correlation_id="corr-1",
    task_id="task-1",
    agent="open-code",
    phase="3",
)
OUTRO_CONTEXTO = EventContext(
    correlation_id="corr-2",
    task_id="task-2",
    agent="open-code",
    phase="3",
)


def _settings(tmp_path: Path) -> Settings:
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
            "HCW_EVENT_LOG": "eventos.jsonl",
        },
        base_dir=base,
    )


@contextmanager
def _servidor(
    settings: Settings,
    caminho_eventos: Path,
) -> Iterator[UiServer]:
    servidor = create_server(settings, event_path=caminho_eventos)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def _cabecalhos(servidor: UiServer) -> Mapping[str, str]:
    return {
        "Origin": f"http://127.0.0.1:{servidor.server_port}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }


def _abrir_stream(
    servidor: UiServer,
    consulta: str,
) -> tuple[HTTPConnection, HTTPResponse]:
    ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
    ligacao.request(
        "GET",
        f"{EVENTS_PATH}?{consulta}",
        headers=dict(_cabecalhos(servidor)),
    )
    resposta = ligacao.getresponse()
    resposta.begin()
    return ligacao, resposta


def _proximo_evento(resposta: HTTPResponse) -> dict[str, object]:
    """Lê o próximo quadro `data:` do stream."""
    while True:
        linha = resposta.fp.readline()
        if not linha:
            raise AssertionError("Stream terminou sem quadro de dados.")
        if linha.startswith(b"data: "):
            return json.loads(linha[6:].decode("utf-8"))


def test_stream_filtra_correlacao_e_nivel(tmp_path: Path) -> None:
    caminho = tmp_path / "eventos.jsonl"
    sumidouro = JsonlSink(caminho)
    sumidouro.write(new_event(CONTEXTO, kind="info", message="iniciar"))
    sumidouro.write(
        new_event(CONTEXTO, kind="warn", message="avisar", level=EventLevel.WARNING)
    )
    sumidouro.write(
        new_event(OUTRO_CONTEXTO, kind="warn", message="outro", level=EventLevel.WARNING)
    )

    with _servidor(_settings(tmp_path), caminho) as servidor:
        ligacao, resposta = _abrir_stream(
            servidor, "correlation_id=corr-1&level=warning"
        )
        try:
            evento = _proximo_evento(resposta)
            assert resposta.status == HTTPStatus.OK
            assert resposta.getheader("Content-Type") == "text/event-stream; charset=utf-8"
            assert evento["message"] == "avisar"
            assert evento["correlation_id"] == "corr-1"
            assert evento["level"] == "warning"
        finally:
            resposta.close()
            ligacao.close()


def test_evento_jsonl_aparece_em_menos_de_um_segundo(tmp_path: Path) -> None:
    caminho = tmp_path / "eventos.jsonl"
    sumidouro = JsonlSink(caminho)

    with _servidor(_settings(tmp_path), caminho) as servidor:
        ligacao, resposta = _abrir_stream(
            servidor, "correlation_id=corr-1&level=warning"
        )
        try:
            evento = new_event(
                CONTEXTO,
                kind="warn",
                message="novo aviso",
                level=EventLevel.WARNING,
            )
            inicio = time.monotonic()
            sumidouro.write(evento)
            recebido = _proximo_evento(resposta)
            decorrido = time.monotonic() - inicio

            assert recebido["event_id"] == evento.event_id
            assert decorrido < 1.0
        finally:
            resposta.close()
            ligacao.close()


def test_stream_termina_ao_cancelar_ligacao(tmp_path: Path) -> None:
    caminho = tmp_path / "eventos.jsonl"

    with _servidor(_settings(tmp_path), caminho) as servidor:
        ligacao, resposta = _abrir_stream(servidor, "level=info")
        assert resposta.status == HTTPStatus.OK
        prazo = time.monotonic() + 2
        while servidor.streams == 0 and time.monotonic() < prazo:
            time.sleep(0.02)
        assert servidor.streams == 1

        resposta.close()
        ligacao.close()
        prazo = time.monotonic() + 2
        while servidor.streams != 0 and time.monotonic() < prazo:
            time.sleep(0.02)

        assert servidor.streams == 0


def test_nivel_invalido_devolve_400(tmp_path: Path) -> None:
    caminho = tmp_path / "eventos.jsonl"

    with _servidor(_settings(tmp_path), caminho) as servidor:
        ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
        ligacao.request(
            "GET",
            f"{EVENTS_PATH}?level=critico",
            headers=dict(_cabecalhos(servidor)),
        )
        estado = ligacao.getresponse().status
        ligacao.close()

    assert estado == HTTPStatus.BAD_REQUEST
