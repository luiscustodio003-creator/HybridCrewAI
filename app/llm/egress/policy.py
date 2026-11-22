"""Política de egress: consentimento antes de rede e redacção antes de envio."""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from app.llm.egress.secret_scan import redact_mapping, redact_text

_LOCAIS = frozenset({"localhost", "127.0.0.1", "::1"})


class EgressError(PermissionError):
    """Base para violações da política de saída."""


class CloudDenied(EgressError):
    """Pedido cloud recusado por falta de consentimento."""


class CloudConsent(Protocol):
    """Fonte de consentimento injectada; não gravada em ficheiro."""

    def allows_cloud(self) -> bool:
        """Indica se a cloud foi explicitamente autorizada."""
        ...


@dataclass(frozen=True)
class EgressPolicy:
    """Decide e executa pedidos HTTP com redacção obrigatória."""

    allow_local: bool = True
    allow_cloud: bool = False

    @staticmethod
    def is_local(url: str) -> bool:
        """Identifica apenas destinos loopback explícitos."""
        try:
            partes = urlsplit(url)
        except ValueError:
            return False
        return partes.hostname in _LOCAIS and partes.scheme in {"http", "https"}

    def authorize(self, url: str, consent: CloudConsent | None = None) -> None:
        """Avalia o destino antes de qualquer abertura de socket."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url tem de ser uma string não vazia.")
        if self.allow_local and self.is_local(url):
            return
        if (
            self.allow_cloud
            and consent is not None
            and consent.allows_cloud() is True
        ):
            return
        raise CloudDenied(
            "Pedido cloud recusado: consentimento ausente; "
            "autorize explicitamente com ConsentStore.grant() antes de repetir."
        )

    def send_json(
        self,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object] | str,
        consent: CloudConsent | None = None,
        timeout_s: float = 5.0,
    ) -> tuple[int, str]:
        """Envia JSON redigido, apenas depois de autorizado."""
        self.authorize(url, consent)
        if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
            raise ValueError("timeout_s tem de ser número.")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("timeout_s tem de ser finito e positivo.")
        if isinstance(body, str):
            corpo = body
        elif isinstance(body, Mapping):
            corpo = json.dumps(body, ensure_ascii=False, sort_keys=True)
        else:
            raise TypeError("body tem de ser mapping ou string.")
        cabecalhos = redact_mapping(headers)
        cabecalhos.setdefault("Content-Type", "application/json")
        pedido = urllib.request.Request(
            redact_text(url),
            data=redact_text(corpo).encode("utf-8"),
            headers=cabecalhos,
            method="POST",
        )
        try:
            with urllib.request.urlopen(pedido, timeout=timeout_s) as resposta:
                return resposta.status, resposta.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as erro:
            return erro.code, erro.read().decode("utf-8", errors="replace")
