"""Porta de sessão live e fabrica protegida por consentimento explícito."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.llm.egress import CloudConsent, CloudDenied, EgressPolicy
from app.llm.providers.common import validar_endpoint


@runtime_checkable
class LiveSession(Protocol):
    """Sessão de voz abstrata, sem tipos de SDK externo."""

    def start(self) -> None:
        """Inicia a sessão."""
        ...

    def send(self, payload: bytes) -> None:
        """Envia um bloco de áudio."""
        ...

    def receive(self) -> bytes:
        """Recebe um bloco de áudio."""
        ...

    def close(self) -> None:
        """Fecha a sessão."""
        ...


class LiveSessionUnavailable(RuntimeError):
    """Nenhuma implementação real foi aprovada para esta sessão."""


def create_live_session(
    endpoint: str,
    egress: EgressPolicy,
    consent: CloudConsent | None,
) -> LiveSession:
    """Cria a sessão live apenas quando ADR-0002 e consentimento autorizam."""
    validar_endpoint(endpoint)
    if consent is None or consent.allows_cloud() is not True:
        raise CloudDenied("Sessão live exige consentimento cloud explícito.")
    egress.authorize(endpoint, consent)
    raise LiveSessionUnavailable(
        "Sessão live real indisponível: dependência de voz ainda não aprovada."
    )
