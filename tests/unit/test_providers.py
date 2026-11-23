"""Testes dos adaptadores com servidor HTTP falso e sem dependências externas."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from app.core.config import ConfigError, SecretStr
from app.llm.contracts import ErrorKind, ModelRequest, ProviderError, ProviderKind
from app.llm.egress import CloudDenied, EgressPolicy
from app.llm.providers import (
    GeminiTextProvider,
    LiveSession,
    LiveSessionUnavailable,
    OllamaProvider,
    create_live_session,
)

_MODELO_GEMINI = "modelo-do-pedido"
_MODELO_OLLAMA = "modelo-configurado"
_TOKENS_GEMINI = 7
_TOKENS_OLLAMA = 3


@dataclass
class Captura:
    """Dados recebidos pelo servidor falso."""

    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    method: str = ""
    path: str = ""


class ConsentimentoFalso:
    def __init__(self, permite: bool) -> None:
        self.permite = permite

    def allows_cloud(self) -> bool:
        return self.permite


def _pedido(provider: ProviderKind, prompt: str = "Diz olá") -> ModelRequest:
    return ModelRequest(
        provider=provider, model=_MODELO_GEMINI, prompt=prompt, timeout_s=2.0,
        task_id="HCW-02-010", correlation_id="corr-adaptadores",
    )


@contextmanager
def _servidor(**opcoes: object) -> Iterator[tuple[str, Captura]]:
    resposta = opcoes.get("resposta")
    status = opcoes.get("status", 200)
    atraso = opcoes.get("atraso", 0.0)
    caminho = opcoes.get("caminho", "/api/generate")
    modelo = opcoes.get("modelo", _MODELO_OLLAMA)
    corpo_bruto = opcoes.get("corpo_bruto")
    tipo_conteudo = opcoes.get("tipo_conteudo", "application/json")
    captura = Captura()
    conteudo_resposta = resposta
    if conteudo_resposta is None:
        if caminho == "/generate":
            conteudo_resposta = {"text": "falso", "tokens_used": _TOKENS_GEMINI}
        else:
            conteudo_resposta = {
                "response": "olá local", "done": True, "eval_count": _TOKENS_OLLAMA,
            }

    class Manipulador(BaseHTTPRequestHandler):
        def _responder(self, codigo: int, texto: str, tipo: str) -> None:
            dados = texto.encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)

        def do_POST(self) -> None:
            tamanho = int(self.headers.get("Content-Length", "0"))
            captura.body = self.rfile.read(tamanho).decode("utf-8", errors="replace")
            captura.headers = dict(self.headers.items())
            captura.method = self.command
            captura.path = self.path
            if self.path != caminho:
                self._responder(404, '{"erro":"caminho"}', "application/json")
                return
            try:
                carga: object = json.loads(captura.body)
            except json.JSONDecodeError:
                self._responder(400, '{"erro":"json"}', "application/json")
                return
            if (
                not isinstance(carga, dict)
                or set(carga) != {"model", "prompt", "stream"}
                or not isinstance(carga["prompt"], str)
                or carga["stream"] is not False
            ):
                self._responder(400, '{"erro":"corpo"}', "application/json")
                return
            if carga["model"] != modelo:
                self._responder(404, '{"erro":"modelo"}', "application/json")
                return
            if atraso:
                time.sleep(atraso)
            texto = corpo_bruto
            if texto is None:
                texto = json.dumps(conteudo_resposta, ensure_ascii=False)
            self._responder(status, texto, tipo_conteudo)

        def do_GET(self) -> None:
            captura.method = self.command
            captura.path = self.path
            self._responder(405, '{"erro":"metodo"}', "application/json")

        def log_message(self, formato: str, *argumentos: object) -> None:
            return

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manipulador)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_port}", captura
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def test_gemini_text_valida_pedido_e_payload_redigido() -> None:
    segredo = "ABC123SEGREDO"
    prompt = f"Não reveles isto: api_key={segredo}"
    with _servidor(caminho="/generate", modelo=_MODELO_GEMINI) as (endpoint, captura):
        chave = SecretStr("sk-chave-falsa")
        adaptador = GeminiTextProvider(
            f"{endpoint}/generate", EgressPolicy(), api_key=chave
        )
        resposta = adaptador.complete(_pedido(ProviderKind.GEMINI_TEXT, prompt))
    carga = json.loads(captura.body)
    assert resposta.provider is ProviderKind.GEMINI_TEXT
    assert resposta.text == "falso"
    assert resposta.tokens_used == _TOKENS_GEMINI
    assert resposta.latency_ms >= 0
    assert captura.method == "POST"
    assert captura.path == "/generate"
    assert set(carga) == {"model", "prompt", "stream"}
    assert carga["stream"] is False
    assert segredo not in captura.body
    assert "***REDACTED***" in captura.body
    assert "sk-chave-falsa" not in str(captura.headers)


def test_ollama_aceita_resposta_e_rejeita_provider_diferente() -> None:
    with _servidor() as (endpoint, captura):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        resposta = adaptador.complete(_pedido(ProviderKind.OLLAMA))
        with pytest.raises(ValueError):
            adaptador.complete(_pedido(ProviderKind.GEMINI_TEXT))
    carga = json.loads(captura.body)
    assert resposta.provider is ProviderKind.OLLAMA
    assert resposta.model == _MODELO_OLLAMA
    assert resposta.text == "olá local"
    assert resposta.tokens_used == _TOKENS_OLLAMA
    assert captura.method == "POST"
    assert captura.path == "/api/generate"
    assert set(carga) == {"model", "prompt", "stream"}
    assert carga["stream"] is False


def test_modelo_configurado_e_a_unica_origem_do_corpo() -> None:
    with _servidor() as (endpoint, captura):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        adaptador.complete(_pedido(ProviderKind.OLLAMA))
    carga = json.loads(captura.body)
    assert carga["model"] == _MODELO_OLLAMA
    assert carga["model"] != _MODELO_GEMINI
    assert "HCW-" not in captura.body
    assert "corr-adaptadores" not in captura.body


def test_ollama_sem_modelo_configurado_falha_antes_de_conectar() -> None:
    with pytest.raises(ConfigError, match="HCW_OLLAMA_MODEL"):
        OllamaProvider("http://127.0.0.1:1", EgressPolicy())


def test_ollama_rejeita_modelo_inexistente() -> None:
    with _servidor(modelo="modelo-esperado") as (endpoint, captura):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model="modelo-inexistente")
        with pytest.raises(ProviderError, match="HTTP 404"):
            adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert captura.method == "POST"
    assert captura.path == "/api/generate"


def test_ollama_rejeita_evento_de_streaming() -> None:
    resposta = {"response": "parcial", "done": False}
    with _servidor(resposta=resposta) as (endpoint, _):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        with pytest.raises(ProviderError) as apanhado:
            adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert apanhado.value.kind is ErrorKind.INVALID_RESPONSE
    assert "streaming" in str(apanhado.value).lower()


def test_ollama_rejeita_ndjson_como_resposta_unica() -> None:
    corpo = '{"response":"a","done":false}\n{"response":"b","done":true}\n'
    with _servidor(corpo_bruto=corpo, tipo_conteudo="application/x-ndjson") as (endpoint, _):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        with pytest.raises(ProviderError) as apanhado:
            adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert apanhado.value.kind is ErrorKind.INVALID_RESPONSE
    assert "json" in str(apanhado.value).lower()


def test_ligacao_recusada_tem_erro_de_rede_claro() -> None:
    adaptador = OllamaProvider("http://127.0.0.1:1", EgressPolicy(), model=_MODELO_OLLAMA)
    with pytest.raises(ProviderError) as apanhado:
        adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert apanhado.value.kind in {ErrorKind.NETWORK, ErrorKind.TIMEOUT}
    mensagem = str(apanhado.value).lower()
    assert "rede" in mensagem or "tempo limite" in mensagem


def test_timeout_vira_provider_error_retryable() -> None:
    with _servidor(atraso=0.25) as (endpoint, _):
        pedido = replace(_pedido(ProviderKind.OLLAMA), timeout_s=0.05)
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        with pytest.raises(ProviderError) as apanhado:
            adaptador.complete(pedido)
    assert apanhado.value.kind is ErrorKind.TIMEOUT
    assert apanhado.value.retryable is True


def test_cloud_sem_consentimento_e_negado_antes_do_socket() -> None:
    adaptador = GeminiTextProvider("https://exemplo.invalido/generate", EgressPolicy())
    with pytest.raises(ProviderError) as apanhado:
        adaptador.complete(_pedido(ProviderKind.GEMINI_TEXT))
    assert apanhado.value.kind is ErrorKind.CONSENT
    assert apanhado.value.retryable is False


def test_resposta_invalida_vira_erro_sem_contexto() -> None:
    with _servidor(resposta={"tokens_used": 1}) as (endpoint, _):
        adaptador = OllamaProvider(endpoint, EgressPolicy(), model=_MODELO_OLLAMA)
        with pytest.raises(ProviderError) as apanhado:
            adaptador.complete(_pedido(ProviderKind.OLLAMA))
    assert apanhado.value.kind is ErrorKind.INVALID_RESPONSE
    assert "olá" not in str(apanhado.value)


def test_live_session_tem_protocolo_e_consentimento_obrigatorio() -> None:
    class SessaoFalsa:
        def start(self) -> None:
            return

        def send(self, payload: bytes) -> None:
            return

        def receive(self) -> bytes:
            return b""

        def close(self) -> None:
            return

    assert isinstance(SessaoFalsa(), LiveSession)
    endpoint = "http://127.0.0.1:1/live"
    with pytest.raises(CloudDenied):
        create_live_session(endpoint, EgressPolicy(), None)
    with pytest.raises(LiveSessionUnavailable):
        create_live_session(
            endpoint,
            EgressPolicy(allow_cloud=True),
            ConsentimentoFalso(True),
        )


def test_adaptadores_nao_importam_sdk_externo() -> None:
    raiz = Path(__file__).resolve().parents[2]
    ficheiros = (
        "app/llm/providers/common.py",
        "app/llm/providers/gemini_text.py",
        "app/llm/providers/gemini_live.py",
        "app/llm/providers/ollama.py",
    )
    proibidos = ("litellm", "google.genai", "import ollama", "import requests")
    for relativo in ficheiros:
        texto = (raiz / relativo).read_text(encoding="utf-8")
        for nome in proibidos:
            assert nome not in texto
