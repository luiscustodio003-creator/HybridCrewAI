"""Evidência real da equipa e da aprovação no browser local."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from app.core.config import load_settings
from app.core.events import EventContext, JsonlSink, new_event
from app.ui.server import UiServer, create_server

PlaywrightError: type[Exception]
sync_playwright: object | None
try:
    from playwright.sync_api import Error as _PlaywrightError
    from playwright.sync_api import sync_playwright as _sync_playwright
except ModuleNotFoundError:
    PlaywrightError = RuntimeError
    sync_playwright = None
else:
    PlaywrightError = _PlaywrightError
    sync_playwright = _sync_playwright

if TYPE_CHECKING:
    from playwright.sync_api import (
        Browser,
        Page,
        PlaywrightContextManager,
        Request,
        Response,
    )

    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
TEMPO_ESPERA_MS = 5000
OK = 200
TOTAL_AGENTES = 5
RAIZ = Path(__file__).resolve().parents[2]
CAPTURAS = RAIZ / "screenshots" / "phase-04"


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
def _servidor(settings: Settings, event_path: Path) -> Iterator[UiServer]:
    """Inicia e fecha um servidor real num porto efémero."""
    servidor = create_server(settings, event_path=event_path)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def _registar_pedido(pedidos: list[str], pedido: Request) -> None:
    """Guarda o URL de cada pedido observado pelo browser."""
    pedidos.append(pedido.url)


def _guardar_token(tokens: list[str], resposta: Response) -> None:
    """Captura o token devolvido pela rota de aprovação."""
    if not resposta.url.endswith("/api/approvals") or resposta.status != OK:
        return
    try:
        dados = resposta.json()
    except ValueError:
        return
    if isinstance(dados, dict) and isinstance(dados.get("token"), str):
        tokens.append(dados["token"])


def _capturar(pagina: Page, nome: str) -> Path:
    """Grava uma captura real da página e devolve o caminho."""
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    caminho = CAPTURAS / nome
    pagina.screenshot(path=str(caminho), full_page=True)
    assert caminho.exists() and caminho.stat().st_size > 0
    return caminho


def _esperar_texto(pagina: Page, seletor: str, texto: str) -> None:
    """Espera que um elemento mostre exactamente o texto esperado."""
    pagina.wait_for_function(
        "(args) => document.querySelector(args[0])?.textContent === args[1]",
        arg=[seletor, texto],
        timeout=TEMPO_ESPERA_MS,
    )


def _verificar_sem_segredos(
    pagina: Page, pedidos: list[str], base: str, token: str
) -> None:
    """Confirma ausência de recursos externos, token no DOM e storage."""
    assert pedidos
    externos = [url for url in pedidos if not url.startswith(base)]
    assert externos == [], f"Pedidos externos observados: {externos}"
    assert token not in pagina.url
    assert token not in pagina.content()
    valores = pagina.evaluate(
        "() => Array.from(document.querySelectorAll('input')).map((campo) => campo.value)"
    )
    assert all(token not in valor for valor in valores)
    estado: dict[str, int] = pagina.evaluate(
        "() => ({ local: localStorage.length, sessao: sessionStorage.length })"
    )
    assert estado == {"local": 0, "sessao": 0}


def _aprovar_plano(
    pagina: Page, tarefa: str, correlacao: str, diff_hash: str, tokens: list[str]
) -> Path:
    """Aprova o plano e devolve a captura da aprovação emitida."""
    pagina.locator("#aprovar").wait_for(state="visible", timeout=TEMPO_ESPERA_MS)
    pagina.locator("#aprovacao-tarefa").fill(tarefa)
    pagina.locator("#aprovacao-correlacao").fill(correlacao)
    pagina.locator("#aprovacao-diff").fill(diff_hash)
    with pagina.expect_response(
        lambda resposta: (
            resposta.url.endswith("/api/approvals") and resposta.status == OK
        )
    ) as resposta_aprovacao:
        pagina.locator("#aprovar").click()
    _esperar_texto(pagina, "#estado-aprovacao", "Aprovação emitida.")
    _guardar_token(tokens, resposta_aprovacao.value)
    assert tokens, "A resposta de aprovação não devolveu token."
    return _capturar(pagina, "02-aprovacao.png")


def test_evidencia_equipa_e_aprovacao_no_browser(tmp_path: Path) -> None:
    """Executa o cliente real, aprova um plano e grava capturas verificáveis."""
    if sync_playwright is None:
        pytest.fail(
            "Playwright não instalado: execute "
            "python -m pip install playwright==1.65.2 e depois "
            "python -m playwright install chromium."
        )

    identificador = uuid.uuid4().hex[:8]
    tarefa = f"tarefa-phase04-{identificador}"
    correlacao = f"correlacao-phase04-{identificador}"
    diff_hash = "d" * 64
    caminho_eventos = tmp_path / "logs" / "events.jsonl"
    caminho_eventos.parent.mkdir(parents=True, exist_ok=True)
    contexto = EventContext(
        correlation_id=correlacao,
        task_id=tarefa,
        agent="planeador",
        phase="4",
    )
    sink = JsonlSink(caminho_eventos)

    with _servidor(_settings(tmp_path), caminho_eventos) as servidor:
        base = f"http://127.0.0.1:{servidor.server_port}"
        criar_motor = cast("Callable[[], PlaywrightContextManager]", sync_playwright)
        with criar_motor() as motor:
            try:
                navegador: Browser = motor.chromium.launch(headless=True)
            except PlaywrightError as erro:
                pytest.fail(
                    "Chromium não instalado ou falha ao iniciar: execute "
                    "python -m playwright install chromium. "
                    f"Detalhe: {erro}"
                )
            try:
                pagina = navegador.new_page()
                pagina.set_default_timeout(TEMPO_ESPERA_MS)
                pagina.set_viewport_size({"width": 1280, "height": 900})
                pedidos: list[str] = []
                tokens: list[str] = []
                pagina.on("request", lambda pedido: _registar_pedido(pedidos, pedido))

                resposta = pagina.goto(
                    base, wait_until="domcontentloaded", timeout=TEMPO_ESPERA_MS
                )
                assert resposta is not None and resposta.ok
                pagina.locator("#token").fill(TOKEN_FALSO)
                pagina.locator("#ligar").click()
                _esperar_texto(pagina, "#estado", "Tarefas atualizadas.")
                assert pagina.locator("#aprovar").is_hidden()
                assert pagina.locator("#aprovar").is_disabled()
                sink.write(
                    new_event(
                        contexto,
                        kind="create.plano",
                        message="Plano pronto para aprovação.",
                        data={"diff_hash": diff_hash},
                    )
                )

                pagina.locator("#agentes li").first.wait_for(
                    state="visible", timeout=TEMPO_ESPERA_MS
                )
                assert pagina.locator("#agentes li").count() == TOTAL_AGENTES
                captura_equipa = _capturar(pagina, "01-equipa.png")

                captura_aprovacao = _aprovar_plano(
                    pagina, tarefa, correlacao, diff_hash, tokens
                )
                _verificar_sem_segredos(pagina, pedidos, base, tokens[0])
            finally:
                navegador.close()

    assert captura_equipa.exists()
    assert captura_aprovacao.exists()
