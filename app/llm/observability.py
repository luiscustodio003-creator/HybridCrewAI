"""Registo observável das chamadas ao gateway, com redacção obrigatória."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import cast

from app.llm.contracts import ModelRequest
from app.llm.egress import redact_text

MAX_PREVIEW_CHARS = 60
_SUFIXO = "..."
_STATUS_VALIDOS = frozenset({"ok", "erro"})


@dataclass
class _Estado:
    """Estado partilhado e protegido por lock."""

    caminho: Path | None = None
    sequencia: int = 0


_lock = Lock()
_estado = _Estado()


def configure_observability(path: Path) -> None:
    """Define o ficheiro JSONL onde as chamadas passam a ser registadas."""
    if not isinstance(path, Path):
        raise TypeError("path tem de ser Path.")
    with _lock:
        _estado.caminho = path


def previsualizacao_prompt(prompt: str) -> str:
    """Devolve um trecho curto do prompt após redacção, nunca o prompt completo."""
    if not isinstance(prompt, str):
        raise TypeError("prompt tem de ser string.")
    redigido = redact_text(prompt).replace("\r", " ").replace("\n", " ")
    return f"{redigido[:MAX_PREVIEW_CHARS]}{_SUFIXO}"


def registar_chamada(
    request: ModelRequest,
    *,
    latency_ms: float,
    model: str | None = None,
    tokens_used: int | None = None,
    status: str = "ok",
) -> None:
    """Acrescenta ao JSONL um registo curto e sem segredos."""
    if isinstance(latency_ms, bool) or not isinstance(latency_ms, (int, float)):
        raise TypeError("latency_ms tem de ser número.")
    latencia = float(latency_ms)
    if not math.isfinite(latencia) or latencia < 0:
        raise ValueError("latency_ms tem de ser finito e não negativo.")
    if tokens_used is not None and (
        isinstance(tokens_used, bool) or not isinstance(tokens_used, int) or tokens_used < 0
    ):
        raise ValueError("tokens_used tem de ser inteiro não negativo ou None.")
    if status not in _STATUS_VALIDOS:
        raise ValueError(f"status inválido {status!r}; use 'ok' ou 'erro'.")
    with _lock:
        if _estado.caminho is None:
            return
        _estado.sequencia += 1
        registo: dict[str, object] = {
            "sequence": _estado.sequencia,
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": request.provider.value,
            "model": model or request.model,
            "latency_ms": round(latencia, 3),
            "tokens": tokens_used,
            "task_id": request.task_id,
            "correlation_id": request.correlation_id,
            "status": status,
            "prompt_preview": previsualizacao_prompt(request.prompt),
        }
        linha = json.dumps(registo, ensure_ascii=False, sort_keys=True)
        _estado.caminho.parent.mkdir(parents=True, exist_ok=True)
        with _estado.caminho.open("a", encoding="utf-8") as ficheiro:
            ficheiro.write(f"{linha}\n")


def ler_chamadas(path: Path, correlation_id: str | None = None) -> list[dict[str, object]]:
    """Lê os registos, filtra por correlação e devolve os mais recentes primeiro."""
    if not isinstance(path, Path):
        raise TypeError("path tem de ser Path.")
    if correlation_id is not None and (not isinstance(correlation_id, str) or not correlation_id.strip()):
        raise ValueError("correlation_id tem de ser texto não vazio ou None.")
    with _lock:
        registos = _carregar(path)
    if correlation_id is not None:
        registos = [registo for registo in registos if registo.get("correlation_id") == correlation_id]
    return sorted(registos, key=_sequencia_de, reverse=True)


def _sequencia_de(registo: dict[str, object]) -> int:
    """Obtém a sequência de um registo lido de JSONL."""
    valor = registo.get("sequence", 0)
    if isinstance(valor, int) and not isinstance(valor, bool):
        return valor
    return 0


def _carregar(path: Path) -> list[dict[str, object]]:
    """Lê linhas válidas de um ficheiro JSONL."""
    if not path.exists():
        return []
    registos: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as ficheiro:
        for numero, linha in enumerate(ficheiro, start=1):
            if not linha.strip():
                continue
            try:
                dados = json.loads(linha)
            except json.JSONDecodeError as erro:
                raise ValueError(f"Registo {numero} inválido em {path.name}.") from erro
            if not isinstance(dados, dict):
                raise ValueError(f"Registo {numero} inválido em {path.name}.")
            registos.append(cast("dict[str, object]", dados))
    return registos
