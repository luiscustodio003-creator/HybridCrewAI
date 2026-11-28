"""Testes dos recursos locais do cliente web."""

from __future__ import annotations

from pathlib import Path

from app.ui.server.auth import origem_valida
from app.ui.server.web_assets import WEB_FILES, ler_asset

RAIZ = Path(__file__).resolve().parents[2]
WEB = RAIZ / "app" / "ui" / "web"
RECURSOS = (
    "index.html",
    "styles.css",
    "tasks.js",
    "logs.js",
    "llm_calls.js",
    "chat.js",
    "agents.js",
    "approvals.js",
    "attachments.js",
)


def _texto(nome: str) -> str:
    """Lê um recurso web como texto UTF-8."""
    return (WEB / nome).read_text(encoding="utf-8")


def test_recursos_locais_estao_mapeados() -> None:
    """A página e todos os recursos locais têm rotas conhecidas."""
    assert set(WEB_FILES) == {"/", "/index.html", *(f"/{nome}" for nome in RECURSOS)}
    for nome in RECURSOS:
        assert (WEB / nome).is_file()


def test_recursos_nao_tem_urls_externas() -> None:
    """Nenhum ficheiro servido referencia recursos fora do servidor local."""
    for nome in RECURSOS:
        texto = _texto(nome)
        assert "http://" not in texto
        assert "https://" not in texto


def test_pagina_liga_todos_os_recursos() -> None:
    """O HTML liga o CSS e os scripts locais pela ordem esperada."""
    html = _texto("index.html")
    for nome in RECURSOS[1:]:
        assert nome in html
    assert html.index("tasks.js") < html.index("logs.js")
    assert html.index("logs.js") < html.index("chat.js")


def test_ler_asset_devolve_bytes_e_tipo() -> None:
    """A leitura de um recurso conhecido devolve o conteúdo e o tipo MIME."""
    recurso = ler_asset("/index.html")
    assert recurso is not None
    corpo, tipo = recurso
    assert b"<html" in corpo.lower()
    assert tipo == "text/html; charset=utf-8"


def test_scripts_nao_injetam_html_nem_guardam_token() -> None:
    """O cliente trata dados como texto e não persiste credenciais."""
    for nome in RECURSOS[2:]:
        texto = _texto(nome)
        assert "innerHTML" not in texto
        assert "insertAdjacentHTML" not in texto
        assert "localStorage" not in texto
        assert "sessionStorage" not in texto
        assert "token-falso" not in texto


def test_ler_asset_recusa_caminho_fora_do_mapa() -> None:
    """Um caminho arbitrário não acede a ficheiros fora da pasta web."""
    assert ler_asset("/../app.py") is None
    assert ler_asset("/app.py") is None
    assert ler_asset("/favicon.ico") is None


def test_origem_sem_cabecalho_aceita_apenas_mesma_origem_do_browser() -> None:
    """Pedidos de mesma origem do browser não precisam de cabeçalho Origin."""
    assert origem_valida(None, 8080, "same-origin") is True
    assert origem_valida(None, 8080, "cross-site") is False
    assert origem_valida(None, 8080, None) is False
    assert origem_valida("http://evil.example", 8080, "same-origin") is False


def test_desenho_de_ecras_esta_em_portugues() -> None:
    """O desenho documenta ecrãs, estados e interações em PT-PT."""
    texto = (RAIZ / "DESIGN.md").read_text(encoding="utf-8")
    for seccao in ("# Desenho", "## Ecrãs", "## Estados", "## Interações"):
        assert seccao in texto
