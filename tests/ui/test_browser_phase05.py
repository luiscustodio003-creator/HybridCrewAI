"""Evidência real do anexo em quarentena e da cobertura no browser local."""

from __future__ import annotations

import threading
import uuid
import zipfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
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
        Response,
    )

    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
TEMPO_ESPERA_MS = 5000
OK = 200
RAIZ = Path(__file__).resolve().parents[2]
CAPTURAS = RAIZ / "screenshots" / "phase-05"


@dataclass(frozen=True, slots=True)
class _Cenario:
    """Dados isolados de um cenário de anexos no browser."""

    base: str
    tarefa: str
    correlacao: str
    diff_hash: str
    anexo_local: Path


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração isolada com anexos, ZIP e escrita activos."""
    base = tmp_path / "project"
    base.mkdir()
    ambiente: Mapping[str, str] = {
        "HCW_UI_ENABLED": "true",
        "HCW_UI_TOKEN": TOKEN_FALSO,
        "HCW_ATTACHMENTS": "true",
        "HCW_ZIP_ENABLED": "true",
        "HCW_WORKSPACE_WRITE": "true",
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


def _zip(caminho: Path) -> Path:
    """Cria um ZIP real com subpastas para o input do browser."""
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as arquivo:
        arquivo.writestr("src/a.txt", b"abc")
        arquivo.writestr("src/docs/b.txt", b"defgh")
    return caminho


def _esperar_texto(pagina: Page, seletor: str, texto: str) -> None:
    """Espera que um elemento contenha o texto esperado."""
    pagina.wait_for_function(
        "(args) => document.querySelector(args[0])?.textContent?.includes(args[1]) === true",
        arg=[seletor, texto],
        timeout=TEMPO_ESPERA_MS,
    )


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


def _capturar(pagina: Page, nome: str) -> Path:
    """Grava uma captura real da página e devolve o caminho."""
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    caminho = CAPTURAS / nome
    pagina.screenshot(path=str(caminho), full_page=True)
    assert caminho.exists() and caminho.stat().st_size > 0
    return caminho


def _preparar_evento(
    tmp_path: Path, tarefa: str, correlacao: str, diff_hash: str
) -> Path:
    """Escreve o evento de plano necessário para emitir a aprovação."""
    caminho_eventos = tmp_path / "logs" / "events.jsonl"
    caminho_eventos.parent.mkdir(parents=True, exist_ok=True)
    contexto = EventContext(
        correlation_id=correlacao,
        task_id=tarefa,
        agent="planeador",
        phase="5",
    )
    JsonlSink(caminho_eventos).write(
        new_event(
            contexto,
            kind="create.plano",
            message="Plano pronto para aprovação.",
            data={"diff_hash": diff_hash},
        )
    )
    return caminho_eventos


def _executar_cenario(
    pagina: Page, cenario: _Cenario, pedidos: list[str], tokens: list[str]
) -> Path:
    """Executa o fluxo real de aprovação, anexo e cobertura no browser."""
    pagina.set_default_timeout(TEMPO_ESPERA_MS)
    pagina.set_viewport_size({"width": 1280, "height": 1100})
    pagina.on("request", lambda pedido: pedidos.append(pedido.url))
    resposta = pagina.goto(
        cenario.base, wait_until="domcontentloaded", timeout=TEMPO_ESPERA_MS
    )
    assert resposta is not None and resposta.ok
    pagina.locator("#token").fill(TOKEN_FALSO)
    pagina.locator("#ligar").click()
    _esperar_texto(pagina, "#estado", "Tarefas atualizadas.")
    pagina.locator("#aprovacao-tarefa").fill(cenario.tarefa)
    pagina.locator("#aprovacao-correlacao").fill(cenario.correlacao)
    pagina.locator("#aprovacao-diff").fill(cenario.diff_hash)
    with pagina.expect_response(
        lambda item: item.url.endswith("/api/approvals") and item.status == OK
    ) as resposta_aprovacao:
        pagina.locator("#aprovar").click()
    _esperar_texto(pagina, "#estado-aprovacao", "Aprovação emitida.")
    _guardar_token(tokens, resposta_aprovacao.value)
    assert tokens, "A resposta de aprovação não devolveu token."
    pagina.locator("#anexo-ficheiro").set_input_files(str(cenario.anexo_local))
    with pagina.expect_response(
        lambda item: item.url.endswith("/api/attachments") and item.status == OK
    ):
        pagina.locator("#anexo-enviar").click()
    _esperar_texto(pagina, "#estado-anexo", "quarentena")
    assert "quarentena" in pagina.locator("#mensagens").inner_text()
    with pagina.expect_response(
        lambda item: item.url.endswith("/api/attachments/release") and item.status == OK
    ):
        pagina.locator("#anexo-aprovar").click()
    _esperar_texto(pagina, "#estado-anexo", "Cobertura")
    texto = pagina.locator("#mensagens").inner_text()
    assert "Cobertura" in texto and "src/docs/b.txt" in texto
    captura = _capturar(pagina, "01-anexos.png")
    _verificar_sem_segredos(pagina, pedidos, cenario.base, tokens[0])
    return captura


def test_evidencia_anexos_no_browser(tmp_path: Path) -> None:
    """Executa o cliente real, aprova o plano e liberta um ZIP com cobertura."""
    if sync_playwright is None:
        pytest.fail(
            "Playwright não instalado: execute "
            "python -m pip install playwright==1.65.2 e depois "
            "python -m playwright install chromium."
        )

    identificador = uuid.uuid4().hex[:8]
    tarefa = f"tarefa-ui010-{identificador}"
    correlacao = f"correlacao-ui010-{identificador}"
    diff_hash = "e" * 64
    caminho_eventos = _preparar_evento(tmp_path, tarefa, correlacao, diff_hash)
    anexo_local = _zip(tmp_path / "relatorio.zip")

    with _servidor(_settings(tmp_path), caminho_eventos) as servidor:
        cenario = _Cenario(
            f"http://127.0.0.1:{servidor.server_port}",
            tarefa,
            correlacao,
            diff_hash,
            anexo_local,
        )
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
                pedidos: list[str] = []
                tokens: list[str] = []
                captura = _executar_cenario(pagina, cenario, pedidos, tokens)
            finally:
                navegador.close()

    assert captura.exists()
