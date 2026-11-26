"""Integração do servidor local da interface web."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import load_settings
from app.ui.server import create_server

if TYPE_CHECKING:
    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
CAMINHO_SAUDE = "/health"
OK = 200
PROIBIDO = 403
NAO_ENCONTRADO = 404


def _settings(tmp_path: Path, **variaveis: str) -> Settings:
    """Carrega configuração isolada para o servidor de teste."""
    base = tmp_path / "project"
    base.mkdir()
    ambiente: Mapping[str, str] = {
        "HCW_UI_ENABLED": "true",
        "HCW_UI_TOKEN": TOKEN_FALSO,
        **variaveis,
    }
    return load_settings(ambiente, base_dir=base)


@contextmanager
def _servidor(settings: Settings) -> Iterator[ThreadingHTTPServer]:
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


def _get_com_cabecalhos(
    servidor: ThreadingHTTPServer,
    caminho: str,
    cabecalhos: Mapping[str, str] | None = None,
) -> tuple[int, str, Mapping[str, str]]:
    """Faz um pedido real e devolve também os cabeçalhos da resposta."""
    ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
    try:
        ligacao.request("GET", caminho, headers=dict(cabecalhos or {}))
        resposta = ligacao.getresponse()
        return (
            resposta.status,
            resposta.read().decode("utf-8"),
            dict(resposta.getheaders()),
        )
    finally:
        ligacao.close()


def _cabecalhos(servidor: ThreadingHTTPServer) -> Mapping[str, str]:
    """Devolve cabeçalhos válidos para o porto do servidor."""
    return {
        "Origin": f"http://127.0.0.1:{servidor.server_port}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }


def test_create_server_vincula_apenas_loopback(tmp_path: Path) -> None:
    servidor = create_server(_settings(tmp_path))
    try:
        assert isinstance(servidor, ThreadingHTTPServer)
        assert servidor.server_address[0] == "127.0.0.1"
        assert servidor.allow_reuse_address is True
    finally:
        servidor.server_close()


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "127.0.0.2"])
def test_create_server_recusa_outro_endereco(tmp_path: Path, host: str) -> None:
    with pytest.raises(ValueError, match="127.0.0.1"):
        create_server(_settings(tmp_path), host=host)


def test_health_responde_quando_interface_esta_habilitada(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, corpo = _get(servidor, CAMINHO_SAUDE, _cabecalhos(servidor))

    assert estado == OK
    assert json.loads(corpo) == {"status": "ok", "phase": 3}


def test_health_nao_responde_quando_interface_esta_desabilitada(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path, HCW_UI_ENABLED="false")) as servidor:
        estado, _ = _get(servidor, CAMINHO_SAUDE)

    assert estado == NAO_ENCONTRADO


def test_caminho_desconhecido_devolve_404(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _get(servidor, "/desconhecido")

    assert estado == NAO_ENCONTRADO


def test_pagina_local_e_servida_sem_autenticacao(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, corpo, cabecalhos = _get_com_cabecalhos(servidor, "/")

    assert estado == OK
    assert "<html" in corpo.lower()
    assert cabecalhos["Content-Type"] == "text/html; charset=utf-8"
    assert cabecalhos["Cache-Control"] == "no-store"
    assert "default-src 'self'" in cabecalhos["Content-Security-Policy"]


def test_recurso_local_desconhecido_devolve_404(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _get(servidor, "/favicon.ico")

    assert estado == NAO_ENCONTRADO


def test_pagina_local_nao_e_servida_com_interface_desabilitada(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path, HCW_UI_ENABLED="false")) as servidor:
        estado, _ = _get(servidor, "/")

    assert estado == NAO_ENCONTRADO


def test_pedido_de_mesma_origem_do_browser_e_aceite(tmp_path: Path) -> None:
    cabecalhos = {
        "Authorization": f"Bearer {TOKEN_FALSO}",
        "Sec-Fetch-Site": "same-origin",
    }
    with _servidor(_settings(tmp_path)) as servidor:
        estado, corpo = _get(servidor, CAMINHO_SAUDE, cabecalhos)

    assert estado == OK
    assert '"status": "ok"' in corpo


def test_pedido_de_origem_cruzada_e_recusado(tmp_path: Path) -> None:
    cabecalhos = {
        "Authorization": f"Bearer {TOKEN_FALSO}",
        "Sec-Fetch-Site": "cross-site",
    }
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _get(servidor, CAMINHO_SAUDE, cabecalhos)

    assert estado == PROIBIDO


def test_servidor_usar_apenas_biblioteca_padrao() -> None:
    root = Path(__file__).resolve().parents[2]
    package = root / "app" / "ui" / "server"
    permitidos = {
        "__future__",
        "agents",
        "app",
        "approvals",
        "collections",
        "contextlib",
        "dataclasses",
        "datetime",
        "hmac",
        "http",
        "json",
        "pathlib",
        "select",
        "socket",
        "sqlite3",
        "threading",
        "time",
        "typing",
        "urllib",
    }
    for source in package.glob("*.py"):
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.startswith(("import ", "from ")):
                modulo = line.split()[1].split(".")[0]
                assert modulo in permitidos, (
                    f"{source.name}: importação externa {modulo}"
                )


def test_modulo_tem_documentacao_obrigatoria() -> None:
    root = Path(__file__).resolve().parents[2]
    package = root / "app" / "ui" / "server"
    assert (package / "README.txt").is_file()
    manifest = (package / "module.yaml").read_text(encoding="utf-8")
    for key in ("name:", "purpose:", "public_api:", "depends_on:"):
        assert key in manifest
