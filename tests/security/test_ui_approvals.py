"""Segurança da aprovação exposta na interface local."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from agents.definitions import load_agent_definitions

from app.core.config import load_settings
from app.ui.server import create_server, ler_asset

if TYPE_CHECKING:
    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
TAREFA = "tarefa-seguranca-010"
CORRELACAO = "correlacao-seguranca-010"
DIFF_HASH = "b" * 64
OK = 200
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
def _servidor(settings: Settings) -> Iterator[object]:
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


def _pedido(
    servidor: object,
    metodo: str,
    caminho: str,
    corpo: bytes | None = None,
) -> tuple[int, str]:
    """Faz um pedido autenticado ao servidor local."""
    porta = int(servidor.server_port)
    cabecalhos = {
        "Origin": f"http://127.0.0.1:{porta}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }
    ligacao = HTTPConnection("127.0.0.1", porta, timeout=2)
    try:
        ligacao.request(metodo, caminho, body=corpo, headers=cabecalhos)
        resposta = ligacao.getresponse()
        return resposta.status, resposta.read().decode("utf-8")
    finally:
        ligacao.close()


def test_recursos_estaticos_nao_contem_token_de_teste() -> None:
    """Nenhum ficheiro servido ao browser inclui o token secreto."""
    for caminho in (
        "/",
        "/index.html",
        "/styles.css",
        "/tasks.js",
        "/logs.js",
        "/llm_calls.js",
        "/chat.js",
        "/agents.js",
        "/approvals.js",
    ):
        recurso = ler_asset(caminho)
        assert recurso is not None, caminho
        assert TOKEN_FALSO.encode("utf-8") not in recurso[0], caminho


def test_agentes_nao_devolvem_instrucoes_completas(tmp_path: Path) -> None:
    """A listagem não expõe o texto que guia cada agente."""
    definicoes = load_agent_definitions()
    fragmento = definicoes[0].texto[:32].strip()
    with _servidor(_settings(tmp_path)) as servidor:
        estado, texto = _pedido(servidor, "GET", "/api/agents")

    assert estado == OK
    assert "texto" not in texto
    assert fragmento not in texto


def test_aprovacao_recusa_campo_extra(tmp_path: Path) -> None:
    """Um campo adicional não pode alterar o contrato de emissão."""
    corpo = json.dumps(
        {
            "task_id": TAREFA,
            "correlation_id": CORRELACAO,
            "diff_hash": DIFF_HASH,
            "aprovado": True,
        }
    ).encode("utf-8")
    with _servidor(_settings(tmp_path)) as servidor:
        estado, texto = _pedido(servidor, "POST", "/api/approvals", corpo)

    assert estado == ERRO
    assert "token" not in texto.lower()


@pytest.mark.parametrize("diff", ["", "curto", "C" * 64])
def test_aprovacao_recusa_diff_invalido(tmp_path: Path, diff: str) -> None:
    """O hash do diff tem de ser SHA-256 hexadecimal em minúsculas."""
    corpo = json.dumps(
        {"task_id": TAREFA, "correlation_id": CORRELACAO, "diff_hash": diff}
    ).encode("utf-8")
    with _servidor(_settings(tmp_path)) as servidor:
        estado, texto = _pedido(servidor, "POST", "/api/approvals", corpo)

    assert estado == ERRO
    assert "token" not in texto.lower()


def test_html_nao_contem_token(tmp_path: Path) -> None:
    """A página servida não contém qualquer valor de token."""
    with _servidor(_settings(tmp_path)) as servidor:
        estado, html = _pedido(servidor, "GET", "/")

    assert estado == OK
    assert TOKEN_FALSO not in html
