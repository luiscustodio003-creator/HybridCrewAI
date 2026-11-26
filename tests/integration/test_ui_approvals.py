"""Integração das rotas de equipa e aprovação da interface local."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import load_settings
from app.ui.server import UiServer, create_server
from app.ui.server.routes_chat import MAX_CORPO_BYTES

if TYPE_CHECKING:
    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
AGENTES_IDS = {
    "planeador",
    "arquitecto",
    "implementador",
    "revisor",
    "relator",
}
TAREFA = "tarefa-ui-010"
CORRELACAO = "correlacao-ui-010"
DIFF_HASH = "a" * 64
OK = 200
NAO_AUTORIZADO = 401
PROIBIDO = 403
ERRO = 400


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração isolada para o servidor de teste."""
    base = tmp_path / "project"
    base.mkdir()
    ambiente: Mapping[str, str] = {
        "HCW_UI_ENABLED": "true",
        "HCW_UI_TOKEN": TOKEN_FALSO,
    }
    return load_settings(ambiente, base_dir=base)


@contextmanager
def _servidor(settings: Settings) -> Iterator[UiServer]:
    """Inicia e fecha um servidor real num porto efémero."""
    servidor = create_server(settings)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def _porta(servidor: UiServer) -> int:
    """Lê o porto do servidor sem depender da classe concreta."""
    return int(servidor.server_port)


def _cabecalhos(servidor: UiServer) -> Mapping[str, str]:
    """Devolve cabeçalhos válidos para o porto do servidor."""
    return {
        "Origin": f"http://127.0.0.1:{_porta(servidor)}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }


def _pedido(
    servidor: UiServer,
    metodo: str,
    caminho: str,
    cabecalhos: Mapping[str, str],
    corpo: bytes | None = None,
) -> tuple[int, str]:
    """Faz um pedido HTTP real ao servidor local."""
    ligacao = HTTPConnection("127.0.0.1", _porta(servidor), timeout=2)
    try:
        ligacao.request(metodo, caminho, body=corpo, headers=dict(cabecalhos))
        resposta = ligacao.getresponse()
        return resposta.status, resposta.read().decode("utf-8")
    finally:
        ligacao.close()


def _corpo(
    tarefa: str = TAREFA, correlacao: str = CORRELACAO, diff: str = DIFF_HASH
) -> bytes:
    """Serializa um pedido de aprovação válido."""
    return json.dumps(
        {"task_id": tarefa, "correlation_id": correlacao, "diff_hash": diff}
    ).encode("utf-8")


def test_get_agentes_lista_equipa_sem_prompt(tmp_path: Path) -> None:
    """A rota de equipa expõe metadados, mas nunca as instruções completas."""
    with _servidor(_settings(tmp_path)) as servidor:
        estado, texto = _pedido(servidor, "GET", "/api/agents", _cabecalhos(servidor))

    assert estado == OK
    agentes = json.loads(texto)
    assert {agente["agent_id"] for agente in agentes} == AGENTES_IDS
    for agente in agentes:
        assert set(agente) == {
            "agent_id",
            "nome",
            "versao",
            "entrada",
            "saida",
            "ferramentas",
        }
        assert isinstance(agente["ferramentas"], list)


@pytest.mark.parametrize(
    ("cabecalhos", "esperado"),
    [
        ({}, PROIBIDO),
        (
            {"Authorization": f"Bearer {TOKEN_FALSO}", "Origin": "http://127.0.0.1:1"},
            PROIBIDO,
        ),
        ({"Authorization": "Bearer errado"}, PROIBIDO),
    ],
)
def test_get_agentes_exige_bearer_e_origem(
    tmp_path: Path,
    cabecalhos: Mapping[str, str],
    esperado: int,
) -> None:
    """A listagem da equipa recusa pedidos sem autenticação local válida."""
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _pedido(servidor, "GET", "/api/agents", cabecalhos)

    assert estado == esperado


def test_get_agentes_exige_bearer_com_origem_valida(tmp_path: Path) -> None:
    """Com origem válida, a listagem exige ainda o bearer da interface."""
    with _servidor(_settings(tmp_path)) as servidor:
        cabecalhos = {"Origin": f"http://127.0.0.1:{servidor.server_port}"}
        estado, _ = _pedido(servidor, "GET", "/api/agents", cabecalhos)

    assert estado == NAO_AUTORIZADO


def test_post_approvals_emite_token_valido(tmp_path: Path) -> None:
    """A emissão devolve um token ligado à tarefa, correlação e diff."""
    with _servidor(_settings(tmp_path)) as servidor:
        estado, texto = _pedido(
            servidor,
            "POST",
            "/api/approvals",
            _cabecalhos(servidor),
            _corpo(),
        )
        registro = json.loads(texto)
        tokens = servidor.tokens

    assert estado == OK
    assert set(registro) == {
        "task_id",
        "correlation_id",
        "diff_hash",
        "emitida_em",
        "expira_em",
        "token",
    }
    assert registro["task_id"] == TAREFA
    assert registro["diff_hash"] == DIFF_HASH
    validado = tokens.validar(registro["token"], TAREFA, DIFF_HASH)
    assert validado.correlation_id == CORRELACAO


@pytest.mark.parametrize(
    ("cabecalhos", "corpo", "esperado"),
    [
        ({}, _corpo(), PROIBIDO),
        (
            {"Authorization": f"Bearer {TOKEN_FALSO}", "Origin": "http://127.0.0.1:1"},
            _corpo(),
            PROIBIDO,
        ),
        (None, _corpo(diff="curto"), ERRO),
        (
            None,
            json.dumps({**json.loads(_corpo()), "approved": True}).encode("utf-8"),
            ERRO,
        ),
        ({}, b"x" * MAX_CORPO_BYTES, PROIBIDO),
    ],
)
def test_post_approvals_recusa_pedidos_invalidos(
    tmp_path: Path,
    cabecalhos: Mapping[str, str] | None,
    corpo: bytes,
    esperado: int,
) -> None:
    """A rota recusa credenciais inválidas e dados fora do contrato."""
    with _servidor(_settings(tmp_path)) as servidor:
        efetivos = _cabecalhos(servidor) if cabecalhos is None else cabecalhos
        estado, _ = _pedido(servidor, "POST", "/api/approvals", efetivos, corpo)

    assert estado == esperado


def test_post_approvals_exige_bearer_com_origem_valida(tmp_path: Path) -> None:
    """Com origem válida, a emissão exige ainda o bearer da interface."""
    with _servidor(_settings(tmp_path)) as servidor:
        cabecalhos = {"Origin": f"http://127.0.0.1:{servidor.server_port}"}
        estado, _ = _pedido(servidor, "POST", "/api/approvals", cabecalhos, _corpo())

    assert estado == NAO_AUTORIZADO
