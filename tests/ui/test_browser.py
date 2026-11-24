"""Evidência real da interface web local em Chromium."""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from app.core.config import load_settings
from app.core.events import EventContext, EventLevel, JsonlSink, new_event
from app.llm import ModelRequest, ProviderKind, registar_chamada
from app.ui.server import create_server

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
    from playwright.sync_api import Browser, Page, PlaywrightContextManager, Request

    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
LIMITE_EVENTO_S = 1.0
TEMPO_ESPERA_MS = 5000
TEMPO_EVENTO_MS = 1000
RAIZ = Path(__file__).resolve().parents[2]
CAPTURAS = RAIZ / "screenshots" / "phase-03"


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
def _servidor(settings: Settings, event_path: Path) -> Iterator[ThreadingHTTPServer]:
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


def _preparar_llm(caminho: Path, correlacao: str, marcador: str) -> None:
    """Regista chamadas observáveis com e sem correspondência de filtro."""
    correspondente = ModelRequest(
        provider=ProviderKind.FAKE,
        model="fake-model",
        prompt=f"{marcador} verificação local",
        timeout_s=5.0,
        task_id="tarefa-ui",
        correlation_id=correlacao,
    )
    registar_chamada(correspondente, latency_ms=12.0, tokens_used=7)
    outro = ModelRequest(
        provider=ProviderKind.FAKE,
        model="fake-model",
        prompt="sem correspondencia",
        timeout_s=5.0,
        task_id="tarefa-ui",
        correlation_id="correlacao-outra",
    )
    registar_chamada(outro, latency_ms=3.0)
    assert caminho.exists()


def _preparar_pagina(pagina: Page, base: str, marcador_llm: str) -> None:
    """Abre a página local e liga os quatro painéis com o token falso."""
    pagina.set_default_timeout(TEMPO_ESPERA_MS)
    pagina.set_viewport_size({"width": 1280, "height": 900})
    resposta = pagina.goto(base, wait_until="domcontentloaded", timeout=TEMPO_ESPERA_MS)
    assert resposta is not None and resposta.ok
    pagina.locator("#token").fill(TOKEN_FALSO)
    pagina.locator("#ligar").click()
    _esperar_texto(pagina, "#estado", "Tarefas atualizadas.")
    for seletor in ("#tarefas", "#eventos", "#llm", "#mensagens"):
        pagina.locator(seletor).wait_for(state="attached")
    pagina.locator("#llm li", has_text=marcador_llm).wait_for(
        state="visible", timeout=TEMPO_ESPERA_MS
    )


def _preparar_eventos(
    sink: JsonlSink,
    contexto: EventContext,
    outro_contexto: EventContext,
    pagina: Page,
    correlacao: str,
) -> None:
    """Escreve eventos filtrados e inicia o fluxo no browser."""
    sink.write(
        new_event(
            outro_contexto,
            kind="ui-test",
            message="ignorado-correlacao",
            level=EventLevel.INFO,
        )
    )
    sink.write(
        new_event(
            contexto,
            kind="ui-test",
            message="ignorado-nivel",
            level=EventLevel.ERROR,
        )
    )
    pagina.locator("#evento-correlacao").fill(correlacao)
    pagina.locator("#evento-nivel").select_option("info")
    pagina.wait_for_function(
        "() => !document.querySelector('#parar-eventos').disabled",
        timeout=TEMPO_ESPERA_MS,
    )
    pagina.locator("#parar-eventos").click()
    pagina.wait_for_function(
        "() => !document.querySelector('#iniciar-eventos').disabled",
        timeout=TEMPO_ESPERA_MS,
    )
    pagina.locator("#iniciar-eventos").click()
    pagina.wait_for_function(
        "() => !document.querySelector('#parar-eventos').disabled",
        timeout=TEMPO_ESPERA_MS,
    )


def _verificar_evento(
    sink: JsonlSink,
    contexto: EventContext,
    pagina: Page,
    marcador: str,
) -> float:
    """Mede o tempo real entre gravar o evento e o browser o mostrar."""
    inicio = time.perf_counter()
    sink.write(
        new_event(
            contexto,
            kind="ui-test",
            message=marcador,
            level=EventLevel.INFO,
        )
    )
    pagina.locator("#eventos li", has_text=marcador).wait_for(
        state="visible", timeout=TEMPO_EVENTO_MS
    )
    latencia = time.perf_counter() - inicio
    pagina.wait_for_timeout(300)
    assert pagina.locator("#eventos li").count() == 1
    texto = pagina.locator("#eventos li").first.inner_text()
    assert "ignorado-correlacao" not in texto
    assert "ignorado-nivel" not in texto
    assert latencia < LIMITE_EVENTO_S, f"Evento visível em {latencia:.3f}s."
    return latencia


def _verificar_llm(pagina: Page, correlacao: str, marcador: str) -> None:
    """Confirma que o filtro de correlação mostra só a chamada esperada."""
    pagina.locator("#llm-correlacao").fill(correlacao)
    pagina.locator("#atualizar-llm").click()
    pagina.locator("#llm li", has_text=marcador).wait_for(state="visible", timeout=TEMPO_ESPERA_MS)
    assert pagina.locator("#llm li").count() == 1


def _verificar_chat(pagina: Page, tarefa: str, correlacao: str, mensagem: str) -> None:
    """Envia uma mensagem real e confirma a resposta no ecrã."""
    pagina.locator("#chat-tarefa").fill(tarefa)
    pagina.locator("#chat-correlacao").fill(correlacao)
    pagina.locator("#chat-mensagem").fill(mensagem)
    pagina.locator("#formulario-chat button[type=submit]").click()
    pagina.locator("#mensagens li", has_text=mensagem).wait_for(
        state="visible", timeout=TEMPO_ESPERA_MS
    )
    _esperar_texto(pagina, "#estado", "Mensagem enviada.")


def _capturar(pagina: Page, nome: str) -> Path:
    """Grava uma captura real da página e devolve o caminho."""
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    caminho = CAPTURAS / nome
    pagina.screenshot(path=str(caminho), full_page=True)
    assert caminho.exists() and caminho.stat().st_size > 0
    return caminho


def _registar_pedido(pedidos: list[str], pedido: Request) -> None:
    """Guarda o URL de cada pedido observado pelo browser."""
    pedidos.append(pedido.url)


def _esperar_texto(pagina: Page, seletor: str, texto: str) -> None:
    """Espera que um elemento mostre exactamente o texto esperado."""
    pagina.wait_for_function(
        "(args) => document.querySelector(args[0])?.textContent === args[1]",
        arg=[seletor, texto],
        timeout=TEMPO_ESPERA_MS,
    )


def _verificar_sem_segredos(pagina: Page, pedidos: list[str], base: str) -> None:
    """Confirma ausência de recursos externos, token no URL e storage."""
    assert pedidos
    externos = [url for url in pedidos if not url.startswith(base)]
    assert externos == [], f"Pedidos externos observados: {externos}"
    assert TOKEN_FALSO not in pagina.url
    estado: dict[str, int] = pagina.evaluate(
        "() => ({ local: localStorage.length, sessao: sessionStorage.length })"
    )
    assert estado == {"local": 0, "sessao": 0}


def test_evidencia_real_no_browser(tmp_path: Path) -> None:
    """Executa o cliente real em Chromium e grava capturas verificáveis."""
    if sync_playwright is None:
        pytest.fail(
            "Playwright não instalado: execute "
            "python -m pip install playwright==1.65.2 e depois "
            "python -m playwright install chromium."
        )

    identificador = uuid.uuid4().hex[:8]
    correlacao = f"ui-{identificador}"
    tarefa = f"tarefa-{identificador}"
    marcador_evento = f"EVENTO-REAL-{identificador}"
    marcador_llm = f"LLM-REAL-{identificador}"
    mensagem = f"Mensagem real {identificador}"
    caminho_eventos = tmp_path / "logs" / "events.jsonl"
    caminho_eventos.parent.mkdir(parents=True, exist_ok=True)

    caminho_llm = caminho_eventos.parent / "llm_calls.jsonl"
    with _servidor(_settings(tmp_path), caminho_eventos) as servidor:
        _preparar_llm(caminho_llm, correlacao, marcador_llm)
        contexto = EventContext(
            correlation_id=correlacao,
            task_id=tarefa,
            agent="teste-ui",
            phase="3",
        )
        outro_contexto = EventContext(
            correlation_id="correlacao-outra",
            task_id=tarefa,
            agent="teste-ui",
            phase="3",
        )
        sink = JsonlSink(caminho_eventos)
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
                pedidos: list[str] = []
                pagina.on("request", lambda pedido: _registar_pedido(pedidos, pedido))
                _preparar_pagina(pagina, base, marcador_llm)
                _preparar_eventos(sink, contexto, outro_contexto, pagina, correlacao)
                latencia = _verificar_evento(sink, contexto, pagina, marcador_evento)
                captura_eventos = _capturar(pagina, "01-eventos.png")
                _verificar_llm(pagina, correlacao, marcador_llm)
                _verificar_chat(pagina, tarefa, correlacao, mensagem)
                captura_chat = _capturar(pagina, "02-chat.png")
                _verificar_sem_segredos(pagina, pedidos, base)
            finally:
                navegador.close()

    assert latencia < LIMITE_EVENTO_S
    assert captura_eventos.exists()
    assert captura_chat.exists()
