"""Integração da listagem persistida de tarefas na interface web."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import load_settings
from app.core.tasks import SqliteTaskStore, Task, TaskSpec, TaskStatus, new_task
from app.ui.server import create_server
from app.ui.server.routes_tasks import serializar_tarefa

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
CAMINHO_TAREFAS = "/api/tasks"
OK = 200
NAO_AUTORIZADO = 401


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração isolada com a interface habilitada."""
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {"HCW_UI_ENABLED": "true", "HCW_UI_TOKEN": TOKEN_FALSO},
        base_dir=base,
    )


def _tarefa(chave: str = "HCW-03-005:integracao") -> Task:
    """Cria uma tarefa válida para os testes."""
    return new_task(
        TaskSpec(
            title="Listar tarefas",
            description="Expor histórico persistido",
            agent="open-code",
            phase="3",
            chave=chave,
            status=TaskStatus.RUNNING,
        )
    )


@contextmanager
def _servidor(
    settings: Settings,
    store: SqliteTaskStore,
) -> Iterator[ThreadingHTTPServer]:
    """Inicia e fecha um servidor real com o store indicado."""
    servidor = create_server(settings, store=store)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def _get(
    servidor: ThreadingHTTPServer,
    caminho: str,
    cabecalhos: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    """Faz um pedido HTTP real ao servidor local."""
    ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
    try:
        ligacao.request("GET", caminho, headers=dict(cabecalhos or {}))
        resposta = ligacao.getresponse()
        return resposta.status, resposta.read().decode("utf-8")
    finally:
        ligacao.close()


def _cabecalhos(servidor: ThreadingHTTPServer) -> Mapping[str, str]:
    """Devolve cabeçalhos válidos para o porto do servidor."""
    return {
        "Origin": f"http://127.0.0.1:{servidor.server_port}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }


def test_get_tasks_devolve_historico_do_store(tmp_path: Path) -> None:
    tarefa = _tarefa()
    store = SqliteTaskStore(tmp_path / "tasks.sqlite")
    store.initialize()
    store.save(tarefa)

    with _servidor(_settings(tmp_path), store) as servidor:
        estado, corpo = _get(servidor, CAMINHO_TAREFAS, _cabecalhos(servidor))

    assert estado == OK
    assert json.loads(corpo) == [serializar_tarefa(tarefa)]


def test_historico_sobrevive_a_reinicio_do_servidor(tmp_path: Path) -> None:
    tarefa = _tarefa("HCW-03-005:reinicio")
    caminho = tmp_path / "historico.sqlite"
    store = SqliteTaskStore(caminho)
    store.initialize()
    store.save(tarefa)
    settings = _settings(tmp_path)

    with _servidor(settings, store) as primeiro:
        primeiro_estado, primeiro_corpo = _get(
            primeiro, CAMINHO_TAREFAS, _cabecalhos(primeiro)
        )

    with _servidor(settings, SqliteTaskStore(caminho)) as segundo:
        segundo_estado, segundo_corpo = _get(
            segundo, CAMINHO_TAREFAS, _cabecalhos(segundo)
        )

    assert primeiro_estado == OK
    assert segundo_estado == OK
    assert json.loads(primeiro_corpo) == json.loads(segundo_corpo)


def test_parametros_de_consulta_nao_alteram_tarefas(tmp_path: Path) -> None:
    tarefa = _tarefa("HCW-03-005:somente-leitura")
    store = SqliteTaskStore(tmp_path / "somente-leitura.sqlite")
    store.initialize()
    store.save(tarefa)
    antes = serializar_tarefa(tarefa)

    with _servidor(_settings(tmp_path), store) as servidor:
        estado, corpo = _get(
            servidor,
            "/api/tasks?write=true&title=alterado",
            _cabecalhos(servidor),
        )

    assert estado == OK
    assert json.loads(corpo) == [antes]
    gravada = store.get(tarefa.task_id)
    assert gravada is not None
    assert gravada.title == antes["title"]


def test_tasks_sem_token_devolve_401(tmp_path: Path) -> None:
    store = SqliteTaskStore(tmp_path / "sem-token.sqlite")

    with _servidor(_settings(tmp_path), store) as servidor:
        origem = _cabecalhos(servidor)["Origin"]
        estado, _ = _get(servidor, CAMINHO_TAREFAS, {"Origin": origem})

    assert estado == NAO_AUTORIZADO
