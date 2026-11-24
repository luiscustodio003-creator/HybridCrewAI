"""Testes da observabilidade das chamadas ao gateway de modelos."""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from http import HTTPStatus
from http.client import HTTPConnection
from pathlib import Path

import pytest

from app.core.config import load_settings
from app.llm import (
    configure_observability,
    ler_chamadas,
    previsualizacao_prompt,
    registar_chamada,
)
from app.llm.contracts import ModelRequest, ProviderError, ProviderKind
from app.llm.egress import CloudConsent, CloudDenied, EgressPolicy
from app.llm.providers.common import ContextoEnvio, post_json
from app.ui.server import create_server
from app.ui.server.routes_llm_calls import LLM_CALLS_PATH, analisar_filtro_correlacao

TOKEN_FALSO = "token-falso-com-16"
LATENCIA_MS = 12.5
TOKENS = 7
LIMITE_PREVIEW = 90


class _EgressSucesso(EgressPolicy):
    def send_json(
        self,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | str,
        consent: CloudConsent | None = None,
        timeout_s: float = 5.0,
    ) -> tuple[int, str]:
        return 200, '{"text":"ok","tokens_used":7}'


class _EgressRecusado(EgressPolicy):
    def send_json(
        self,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | str,
        consent: CloudConsent | None = None,
        timeout_s: float = 5.0,
    ) -> tuple[int, str]:
        raise CloudDenied("pedido recusado")


def _pedido(correlacao: str = "corr-1") -> ModelRequest:
    return ModelRequest(
        provider=ProviderKind.OLLAMA,
        model="qwen3.5:4b",
        prompt="resuma API_TOKEN=segredo-falso-123 e " + "conteudo " * 30,
        timeout_s=1.0,
        task_id="task-1",
        correlation_id=correlacao,
    )


def _linhas(caminho: Path) -> list[dict[str, object]]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines()]


def _texto(registo: dict[str, object], chave: str) -> str:
    valor = registo[chave]
    assert isinstance(valor, str)
    return valor


def _inteiro(registo: dict[str, object], chave: str) -> int:
    valor = registo[chave]
    assert isinstance(valor, int)
    return valor


def test_previsualizacao_redige_e_trunca(tmp_path: Path) -> None:
    prompt = "API_TOKEN=segredo-falso-123 " + "conteudo " * 40

    resultado = previsualizacao_prompt(prompt)

    assert "segredo-falso-123" not in resultado
    assert "***REDACTED***" in resultado
    assert resultado.endswith("...")
    assert prompt not in resultado
    assert len(resultado) <= LIMITE_PREVIEW


def test_registar_chamada_escreve_campos_obrigatorios(tmp_path: Path) -> None:
    caminho = tmp_path / "llm_calls.jsonl"
    configure_observability(caminho)

    registar_chamada(
        _pedido(),
        latency_ms=LATENCIA_MS,
        model="qwen3.5:4b",
        tokens_used=TOKENS,
        status="ok",
    )

    registo = _linhas(caminho)[0]
    assert registo["provider"] == "ollama"
    assert registo["model"] == "qwen3.5:4b"
    assert registo["latency_ms"] == LATENCIA_MS
    assert registo["tokens"] == TOKENS
    assert registo["task_id"] == "task-1"
    assert registo["correlation_id"] == "corr-1"
    assert registo["status"] == "ok"
    assert "segredo-falso-123" not in str(registo["prompt_preview"])


def test_post_json_regista_sucesso_com_tokens(tmp_path: Path) -> None:
    caminho = tmp_path / "llm_calls.jsonl"
    configure_observability(caminho)
    pedido = _pedido()

    post_json(
        _EgressSucesso(),
        "http://127.0.0.1:1/api/generate",
        {},
        {"model": "qwen3.5:4b", "prompt": pedido.prompt},
        ContextoEnvio(pedido, None),
    )

    registo = _linhas(caminho)[0]
    assert registo["status"] == "ok"
    assert registo["model"] == "qwen3.5:4b"
    assert registo["tokens"] == TOKENS
    assert _texto(registo, "prompt_preview").endswith("...")


def test_post_json_regista_falha(tmp_path: Path) -> None:
    caminho = tmp_path / "llm_calls.jsonl"
    configure_observability(caminho)

    with pytest.raises(ProviderError):
        post_json(
            _EgressRecusado(),
            "http://127.0.0.1:1/api/generate",
            {},
            {"model": "qwen3.5:4b", "prompt": _pedido().prompt},
            ContextoEnvio(_pedido(), None),
        )

    registo = _linhas(caminho)[0]
    assert registo["status"] == "erro"
    assert registo["tokens"] is None


def test_ler_chamadas_filtra_e_ordena(tmp_path: Path) -> None:
    caminho = tmp_path / "llm_calls.jsonl"
    configure_observability(caminho)
    for correlacao in ("corr-1", "corr-2", "corr-1"):
        registar_chamada(_pedido(correlacao), latency_ms=1.0, status="ok")

    registos = ler_chamadas(caminho, "corr-1")

    assert [registo["correlation_id"] for registo in registos] == ["corr-1", "corr-1"]
    sequencias = [_inteiro(registo, "sequence") for registo in registos]
    assert sequencias[0] > sequencias[1]


def test_analisar_filtro_correlacao_rejeita_repetidos() -> None:
    with pytest.raises(ValueError, match="correlation_id"):
        analisar_filtro_correlacao("correlation_id=corr-1&correlation_id=corr-2")


def test_api_llm_calls_devolve_registos_filtrados(tmp_path: Path) -> None:
    base = tmp_path / "project"
    base.mkdir()
    settings = load_settings(
        {
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
            "HCW_EVENT_LOG": "eventos.jsonl",
        },
        base_dir=base,
    )
    caminho = tmp_path / "llm_calls.jsonl"
    servidor = create_server(settings, event_path=caminho.parent / "eventos.jsonl")
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        registar_chamada(_pedido("corr-1"), latency_ms=3.0, status="ok")
        registar_chamada(_pedido("corr-2"), latency_ms=4.0, status="ok")
        ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
        ligacao.request(
            "GET",
            f"{LLM_CALLS_PATH}?correlation_id=corr-1",
            headers={
                "Origin": f"http://127.0.0.1:{servidor.server_port}",
                "Authorization": f"Bearer {TOKEN_FALSO}",
            },
        )
        resposta = ligacao.getresponse()
        dados = json.loads(resposta.read())
        ligacao.close()

        assert resposta.status == HTTPStatus.OK
        assert resposta.getheader("Content-Type") == "application/json; charset=utf-8"
        assert len(dados) == 1
        assert dados[0]["correlation_id"] == "corr-1"
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def test_api_llm_calls_rejeita_filtro_invalido(tmp_path: Path) -> None:
    base = tmp_path / "project"
    base.mkdir()
    settings = load_settings(
        {
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
            "HCW_EVENT_LOG": "eventos.jsonl",
        },
        base_dir=base,
    )
    servidor = create_server(settings, event_path=tmp_path / "eventos.jsonl")
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        ligacao = HTTPConnection("127.0.0.1", servidor.server_port, timeout=2)
        ligacao.request(
            "GET",
            f"{LLM_CALLS_PATH}?correlation_id=",
            headers={
                "Origin": f"http://127.0.0.1:{servidor.server_port}",
                "Authorization": f"Bearer {TOKEN_FALSO}",
            },
        )
        estado = ligacao.getresponse().status
        ligacao.close()
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)

    assert estado == HTTPStatus.BAD_REQUEST
