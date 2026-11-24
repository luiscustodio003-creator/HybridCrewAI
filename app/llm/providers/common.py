"""Instrumentação comum aos adaptadores HTTP, sem SDK externo."""

from __future__ import annotations

import json
import time
import urllib.error
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from app.llm.contracts import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)
from app.llm.egress import CloudConsent, CloudDenied, EgressPolicy
from app.llm.observability import registar_chamada

_HTTP_ERRO = 400
_HTTP_SERVIDOR = 500
_HTTP_TAXA = 429
_HTTP_TEMPOS = frozenset({408, 504})
_HTTP_AUTENTICACAO = frozenset({401, 403})


@dataclass(frozen=True)
class ContextoEnvio:
    """Pedido e consentimento necessários ao transporte."""

    request: ModelRequest
    consent: CloudConsent | None


class ModelProvider(Protocol):
    """Porta comum implementada pelos adaptadores sem estado."""

    provider: ProviderKind

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Executa um pedido e devolve uma resposta normalizada."""
        ...


def validar_endpoint(endpoint: str) -> str:
    """Valida endereço completo fornecido pela configuração."""
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("endpoint tem de ser texto não vazio.")
    partes = urlsplit(endpoint)
    if partes.scheme not in {"http", "https"} or not partes.netloc:
        raise ValueError("endpoint tem de ser um URL http(s) completo.")
    return endpoint


def validar_adaptador(provider: ProviderKind, request: ModelRequest) -> None:
    """Garante que o pedido foi criado para este adaptador."""
    if request.provider is not provider:
        raise ValueError(
            f"pedido para {request.provider.value!r} não serve {provider.value!r}."
        )


def corpo_pedido(model: str, prompt: str) -> dict[str, object]:
    """Constrói o corpo externo sem identificadores internos nem segredos."""
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }


def _classificar_http(status: int) -> tuple[ErrorKind, bool]:
    if status in _HTTP_AUTENTICACAO:
        return ErrorKind.AUTH, False
    if status == _HTTP_TAXA:
        return ErrorKind.RATE_LIMIT, True
    if status in _HTTP_TEMPOS:
        return ErrorKind.TIMEOUT, True
    if status >= _HTTP_SERVIDOR:
        return ErrorKind.NETWORK, True
    return ErrorKind.INVALID_RESPONSE, False


def _erro(provider: ProviderKind, request: ModelRequest, message: str) -> ProviderError:
    return ProviderError(
        provider, ErrorKind.INVALID_RESPONSE, message, request.task_id, request.correlation_id
    )


def _e_timeout(motivo: object) -> bool:
    texto = str(motivo).lower()
    return isinstance(motivo, TimeoutError) or "timed out" in texto or "timeout" in texto


def _tokens_dos_dados(dados: dict[str, object]) -> int | None:
    """Extrai tokens normalizados ou o contador nativo do adaptador."""
    for chave in ("tokens_used", "eval_count"):
        valor = dados.get(chave)
        if isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0:
            return valor
    return None


def post_json(
    egress: EgressPolicy,
    endpoint: str,
    headers: dict[str, str],
    body: dict[str, object],
    contexto: ContextoEnvio,
) -> dict[str, object]:
    """Envia JSON e regista a chamada, com sucesso ou falha."""
    inicio = time.perf_counter()
    request = contexto.request
    modelo = body.get("model")
    nome_modelo = modelo if isinstance(modelo, str) and modelo.strip() else request.model
    try:
        dados = _post_json(egress, endpoint, headers, body, contexto)
    except Exception:
        registar_chamada(
            request,
            latency_ms=(time.perf_counter() - inicio) * 1000,
            model=nome_modelo,
            status="erro",
        )
        raise
    registar_chamada(
        request,
        latency_ms=(time.perf_counter() - inicio) * 1000,
        model=nome_modelo,
        tokens_used=_tokens_dos_dados(dados),
        status="ok",
    )
    return dados


def _post_json(
    egress: EgressPolicy,
    endpoint: str,
    headers: dict[str, str],
    body: dict[str, object],
    contexto: ContextoEnvio,
) -> dict[str, object]:
    """Envia JSON pela política de egress e devolve o objecto recebido."""
    request = contexto.request
    try:
        status, texto = egress.send_json(
            endpoint, headers, body, contexto.consent, request.timeout_s
        )
    except CloudDenied as erro:
        raise ProviderError(
            request.provider,
            ErrorKind.CONSENT,
            str(erro),
            request.task_id,
            request.correlation_id,
        ) from erro
    except TimeoutError as erro:
        raise ProviderError(
            request.provider,
            ErrorKind.TIMEOUT,
            "Tempo limite esgotado antes da resposta.",
            request.task_id,
            request.correlation_id,
            retryable=True,
        ) from erro
    except urllib.error.URLError as erro:
        mensagem = "Tempo limite esgotado antes da resposta."
        categoria = ErrorKind.TIMEOUT
        if not _e_timeout(erro.reason):
            mensagem = "Falha de rede ao contactar o fornecedor."
            categoria = ErrorKind.NETWORK
        raise ProviderError(
            request.provider,
            categoria,
            mensagem,
            request.task_id,
            request.correlation_id,
            retryable=True,
        ) from erro
    if status >= _HTTP_ERRO:
        categoria, repetivel = _classificar_http(status)
        raise ProviderError(
            request.provider,
            categoria,
            f"HTTP {status}.",
            request.task_id,
            request.correlation_id,
            retryable=repetivel,
        )
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise _erro(request.provider, request, "Resposta não é JSON.") from erro
    if not isinstance(dados, dict):
        raise _erro(request.provider, request, "Resposta JSON não é objecto.")
    return dados


def resposta_modelo(
    provider: ProviderKind,
    request: ModelRequest,
    dados: dict[str, object],
    inicio: float,
) -> ModelResponse:
    """Valida o corpo interno e constrói a resposta imutável."""
    texto = dados.get("text")
    if not isinstance(texto, str) or not texto.strip():
        raise _erro(provider, request, "Resposta sem texto válido.")
    tokens = dados.get("tokens_used")
    if tokens is not None and (
        isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0
    ):
        raise _erro(provider, request, "Resposta com tokens_used inválido.")
    return ModelResponse(
        provider=provider,
        model=request.model,
        text=texto,
        task_id=request.task_id,
        correlation_id=request.correlation_id,
        latency_ms=max(0.0, (time.perf_counter() - inicio) * 1000),
        tokens_used=tokens if isinstance(tokens, int) else None,
    )
