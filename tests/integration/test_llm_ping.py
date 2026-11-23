"""Integração do comando hcw llm ping sem contactar a cloud real."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIMITE = 10
SEGREDO = "sk-falso-nao-e-segredo"
MODELO_LOCAL = "modelo-local"


def _executar(
    *argumentos: str, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    ambiente = os.environ.copy()
    if env is None:
        ambiente.pop("HCW_OLLAMA_MODEL", None)
    else:
        ambiente.update(env)
    return subprocess.run(
        [sys.executable, "-m", "app.cli", "llm", "ping", *argumentos],
        cwd=RAIZ,
        env=ambiente,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=LIMITE,
        check=False,
    )


@contextmanager
def _servidor(*, atraso: float = 0.0) -> Iterator[tuple[str, dict[str, str]]]:
    captura: dict[str, str] = {}

    class Manipulador(BaseHTTPRequestHandler):
        def _responder(self, codigo: int, texto: str) -> None:
            corpo = texto.encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            try:
                self.wfile.write(corpo)
            except OSError:
                return

        def do_POST(self) -> None:
            tamanho = int(self.headers.get("Content-Length", "0"))
            captura["body"] = self.rfile.read(tamanho).decode("utf-8", errors="replace")
            captura["method"] = self.command
            captura["path"] = self.path
            if self.path != "/api/generate":
                self._responder(404, '{"erro":"caminho"}')
                return
            try:
                carga = json.loads(captura["body"])
            except json.JSONDecodeError:
                self._responder(400, '{"erro":"json"}')
                return
            if not isinstance(carga, dict) or set(carga) != {"model", "prompt", "stream"}:
                self._responder(400, '{"erro":"corpo"}')
                return
            if carga["model"] != MODELO_LOCAL or carga["stream"] is not False:
                self._responder(400, '{"erro":"modelo"}')
                return
            if atraso:
                time.sleep(atraso)
            self._responder(
                200,
                json.dumps(
                    {"response": "pong local", "done": True, "eval_count": 2},
                    ensure_ascii=False,
                ),
            )

        def do_GET(self) -> None:
            captura["method"] = self.command
            captura["path"] = self.path
            self._responder(405, '{"erro":"metodo"}')

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


def test_ping_simulado_mostra_latencia_e_redige_prompt() -> None:
    resultado = _executar("--prompt", f"token={SEGREDO}")

    assert resultado.returncode == 0, resultado.stderr
    assert "fornecedor: fake" in resultado.stdout
    assert "latencia_ms:" in resultado.stdout
    assert SEGREDO not in resultado.stdout
    assert "***REDACTED***" in resultado.stdout


def test_ping_local_contacta_ollama_falso_e_nao_reenvia_segredo() -> None:
    with _servidor() as (endpoint, captura):
        resultado = _executar(
            "--provider",
            "ollama",
            "--endpoint",
            endpoint,
            "--prompt",
            f"api_key={SEGREDO}",
            env={"HCW_OLLAMA_MODEL": MODELO_LOCAL},
        )

    carga = json.loads(captura["body"])
    assert resultado.returncode == 0, resultado.stderr
    assert "fornecedor: ollama" in resultado.stdout
    assert "pong local" in resultado.stdout
    assert captura["method"] == "POST"
    assert captura["path"] == "/api/generate"
    assert set(carga) == {"model", "prompt", "stream"}
    assert carga["model"] == MODELO_LOCAL
    assert SEGREDO not in captura["body"]
    assert "***REDACTED***" in captura["body"]


def test_ping_local_sem_modelo_configurado_falha_com_mensagem_clara() -> None:
    resultado = _executar(
        "--provider",
        "ollama",
        "--endpoint",
        "http://127.0.0.1:1",
        "--prompt",
        "Diz olá",
        env={},
    )

    assert resultado.returncode != 0
    assert "HCW_OLLAMA_MODEL" in resultado.stderr
    assert "Diz olá" not in resultado.stderr


def test_ping_cloud_sem_consentimento_falha_sem_mostrar_segredo(
    tmp_path: Path,
) -> None:
    resultado = _executar(
        "--provider",
        "gemini",
        "--endpoint",
        "https://exemplo.invalido/generate",
        "--allow-cloud",
        "--base-dir",
        str(tmp_path),
        "--prompt",
        f"api_key={SEGREDO}",
    )

    assert resultado.returncode != 0
    assert SEGREDO not in resultado.stdout + resultado.stderr
    assert "consentimento" in resultado.stderr.lower()


def test_ping_local_com_timeout_falha_sem_mostrar_segredo() -> None:
    with _servidor(atraso=0.25) as (endpoint, _):
        resultado = _executar(
            "--provider",
            "ollama",
            "--endpoint",
            endpoint,
            "--timeout",
            "0.05",
            "--prompt",
            f"token={SEGREDO}",
            env={"HCW_OLLAMA_MODEL": MODELO_LOCAL},
        )

    assert resultado.returncode != 0
    assert SEGREDO not in resultado.stdout + resultado.stderr
    assert "tempo limite" in resultado.stderr.lower()
