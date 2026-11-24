"""Segurança local do servidor da interface web."""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from app.core.config import load_settings
from app.ui.server import create_server
from app.ui.server.app import _Handler

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from app.core.config import Settings

RAIZ = Path(__file__).resolve().parents[2]
MODELO_AMEACAS = RAIZ / "THREAT_MODEL.md"
RELATORIO_SEGURANCA = RAIZ / "docs" / "reports" / "phase-03-security.md"
RELATORIO_EVIDENCIA = RAIZ / "docs" / "reports" / "phase-03-ui-evidence.md"
TOKEN_FALSO = "token-falso-com-16"
SEGREDO_PROMPT = "prompt-confidencial-que-nao-deve-sair"
CAMINHO_SAUDE = "/health"
CAMINHO_EVENTOS = "/api/events"
NAO_AUTORIZADO = 401
PROIBIDO = 403
OK = 200


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração com interface habilitada e token de teste."""
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
        },
        base_dir=base,
    )


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


@contextmanager
def _capturar_erro() -> Iterator[StringIO]:
    """Captura a saída de erro usada pelo servidor durante os pedidos."""
    original = sys.stderr
    fluxo = StringIO()
    sys.stderr = fluxo
    try:
        yield fluxo
    finally:
        sys.stderr = original


def _get(
    servidor: ThreadingHTTPServer,
    cabecalhos: Mapping[str, str] | None = None,
    caminho: str = CAMINHO_SAUDE,
) -> tuple[int, str]:
    """Faz um pedido autenticado a uma rota local."""
    ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
    try:
        ligacao.request("GET", caminho, headers=dict(cabecalhos or {}))
        resposta = ligacao.getresponse()
        return resposta.status, resposta.read().decode("utf-8")
    finally:
        ligacao.close()


def _cabecalhos(servidor: ThreadingHTTPServer, **extra: str) -> dict[str, str]:
    """Devolve cabeçalhos válidos para o porto do servidor."""
    return {
        "Origin": f"http://127.0.0.1:{servidor.server_port}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
        **extra,
    }


def test_pedido_sem_token_devolve_401_e_nao_executa_rota(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[Any] = []
    original = _Handler._health

    def registar(self: _Handler) -> None:
        chamadas.append(self.path)
        original(self)

    monkeypatch.setattr(_Handler, "_health", registar)
    with _servidor(_settings(tmp_path)) as servidor:
        estado, corpo = _get(servidor, {"Origin": _cabecalhos(servidor)["Origin"]})

    assert estado == NAO_AUTORIZADO
    assert chamadas == []
    assert "ok" not in corpo


@pytest.mark.parametrize(
    ("modelo", "substituir"),
    [
        ("http://127.0.0.1:{porta}", "localhost"),
        ("http://127.0.0.1:{porta}", "127.0.0.2"),
        ("http://127.0.0.1:{porta}", "evil.example"),
        ("https://127.0.0.1:{porta}", None),
    ],
)
def test_origin_fora_do_loopback_devolve_403(
    tmp_path: Path,
    modelo: str,
    substituir: str | None,
) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        porta = servidor.server_port
        origem = modelo.format(porta=porta)
        if substituir is not None:
            origem = origem.replace("127.0.0.1", substituir)
        estado, _ = _get(
            servidor,
            {"Origin": origem, "Authorization": f"Bearer {TOKEN_FALSO}"},
        )

    assert estado == PROIBIDO


def test_events_sem_token_devolve_401(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _get(
            servidor,
            {"Origin": _cabecalhos(servidor)["Origin"]},
            CAMINHO_EVENTOS,
        )

    assert estado == NAO_AUTORIZADO


def test_events_com_origin_falso_devolve_403(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, _ = _get(
            servidor,
            {
                "Origin": "http://evil.example",
                "Authorization": f"Bearer {TOKEN_FALSO}",
            },
            CAMINHO_EVENTOS,
        )

    assert estado == PROIBIDO


def test_pedido_autenticado_devolve_health(tmp_path: Path) -> None:
    with _servidor(_settings(tmp_path)) as servidor:
        estado, corpo = _get(servidor, _cabecalhos(servidor))

    assert estado == OK
    assert '"status": "ok"' in corpo


def test_segredos_nao_aparecem_em_logs_nem_respostas(tmp_path: Path) -> None:
    with _capturar_erro() as logs, _servidor(_settings(tmp_path)) as servidor:
        _, valido = _get(servidor, _cabecalhos(servidor, **{"X-Prompt": SEGREDO_PROMPT}))
        _, sem_token = _get(
            servidor,
            {"Origin": _cabecalhos(servidor)["Origin"], "X-Prompt": SEGREDO_PROMPT},
        )
        _, origem_falsa = _get(
            servidor,
            {
                "Origin": "http://evil.example",
                "Authorization": f"Bearer {TOKEN_FALSO}",
                "X-Prompt": SEGREDO_PROMPT,
            },
        )

    observado = valido + sem_token + origem_falsa + logs.getvalue()
    assert TOKEN_FALSO not in observado
    assert SEGREDO_PROMPT not in observado


def test_modelo_de_ameacas_da_fase_3_liga_ameacas_a_testes_reais() -> None:
    """Verifica token, Origin, loopback e prompt injection no modelo de ameaças."""
    linhas = MODELO_AMEACAS.read_text(encoding="utf-8").splitlines()
    for termo in ("token", "Origin", "127.0.0.1", "prompt injection"):
        correspondencias = [
            linha
            for linha in linhas
            if linha.startswith("|")
            and termo.lower() in linha.lower()
            and "test_" in linha
            and "PASSA" in linha
        ]
        assert correspondencias, termo


def test_relatorios_da_fase_3_documentam_evidencia_sem_segredos() -> None:
    """Exige comandos, ficheiros e capturas sem prompt completo nem token real."""
    texto = RELATORIO_SEGURANCA.read_text(encoding="utf-8")
    assert "Comandos executados" in texto
    assert "tests/security/test_ui_local.py" in texto
    assert "screenshots/phase-03/01-eventos.png" in texto
    for caminho in (RELATORIO_SEGURANCA, RELATORIO_EVIDENCIA):
        conteudo = caminho.read_text(encoding="utf-8")
        assert SEGREDO_PROMPT not in conteudo
        assert f"Bearer {TOKEN_FALSO}" not in conteudo
