"""Modelos imutáveis do runner determinístico de agentes."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from app.llm.contracts import ProviderKind
from app.llm.egress import UntrustedContentError, wrap_untrusted

MAX_RESUMO = 2000
MAX_EVIDENCIA = 200
MAX_ITENS_EVIDENCIA = 20
MAX_RETRIES_PERMITIDAS = 2
CAMPOS_SAIDA = frozenset({"summary", "evidence", "approved"})


class ApprovalState(StrEnum):
    """Estado de aprovação controlado fora do modelo."""

    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class AgentRunError(ValueError):
    """Erro de configuração ou execução do runner."""


class OutputValidationError(AgentRunError):
    """Saída do modelo que não cumpre o contrato."""


class ForgedMarkerError(OutputValidationError):
    """Saída que tenta forjar delimitadores de conteúdo não confiável."""


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    """Limites fixos de uma instância do runner."""

    provider_kind: ProviderKind
    model: str
    timeout_s: float
    max_retries: int = 2

    def __post_init__(self) -> None:
        """Valida fornecedor, modelo, timeout e número de repetições."""
        if not isinstance(self.provider_kind, ProviderKind):
            raise AgentRunError("provider_kind tem de ser ProviderKind.")
        if not isinstance(self.model, str) or not self.model.strip():
            raise AgentRunError("model tem de ser texto não vazio.")
        if isinstance(self.timeout_s, bool) or not isinstance(
            self.timeout_s, (int, float)
        ):
            raise AgentRunError("timeout_s tem de ser número.")
        if not math.isfinite(self.timeout_s) or self.timeout_s <= 0:
            raise AgentRunError("timeout_s tem de ser finito e positivo.")
        if (
            isinstance(self.max_retries, bool)
            or not isinstance(self.max_retries, int)
            or self.max_retries < 0
            or self.max_retries > MAX_RETRIES_PERMITIDAS
        ):
            raise AgentRunError("max_retries tem de ser inteiro entre 0 e 2.")


@dataclass(frozen=True, slots=True)
class AgentRun:
    """Pedido determinístico de execução de um agente local."""

    agent_id: str
    task_id: str
    correlation_id: str
    phase: str
    untrusted: Mapping[str, str] = field(default_factory=dict)
    approval_state: ApprovalState = ApprovalState.PENDENTE

    def __post_init__(self) -> None:
        """Valida identificadores, blocos não confiáveis e aprovação."""
        for nome in ("agent_id", "task_id", "correlation_id", "phase"):
            valor = getattr(self, nome)
            if not isinstance(valor, str) or not valor.strip():
                raise AgentRunError(f"{nome} tem de ser texto não vazio.")
        if not isinstance(self.untrusted, Mapping):
            raise AgentRunError("untrusted tem de ser um mapping.")
        copia: dict[str, str] = {}
        for chave, valor in self.untrusted.items():
            if not isinstance(chave, str) or not isinstance(valor, str):
                raise AgentRunError("Chaves e valores de untrusted têm de ser strings.")
            copia[chave] = valor
        object.__setattr__(self, "untrusted", copia)
        if not isinstance(self.approval_state, ApprovalState):
            raise AgentRunError("approval_state tem de ser ApprovalState.")


@dataclass(frozen=True, slots=True)
class AgentOutput:
    """Saída validada do modelo; aprovação reivindicada é apenas observação."""

    summary: str
    evidence: tuple[str, ...]
    approval_claim: bool = False


def _texto_saida(valor: object, nome: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise OutputValidationError(f"{nome} tem de ser texto não vazio.")
    if len(valor) > MAX_RESUMO:
        raise OutputValidationError(f"{nome} excede o tamanho permitido.")
    try:
        wrap_untrusted(valor)
    except UntrustedContentError as erro:
        raise ForgedMarkerError(f"{nome} contém marcadores proibidos.") from erro
    return valor


def parse_agent_output(texto: str) -> AgentOutput:
    """Converte a resposta do modelo em dados validados, sem a executar."""
    if not isinstance(texto, str):
        raise TypeError("texto tem de ser string.")
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise OutputValidationError("saida nao e json valido.") from erro
    if not isinstance(dados, dict):
        raise OutputValidationError("saida tem de ser um objecto json.")
    desconhecidas = sorted(set(dados) - CAMPOS_SAIDA)
    if desconhecidas:
        raise OutputValidationError(f"chave desconhecida: {desconhecidas[0]}.")
    ausentes = sorted(CAMPOS_SAIDA - {"approved"} - set(dados))
    if ausentes:
        raise OutputValidationError(f"chave em falta: {ausentes[0]}.")
    resumo = _texto_saida(dados["summary"], "summary")
    itens = dados["evidence"]
    if not isinstance(itens, list) or not itens:
        raise OutputValidationError("evidence tem de ser uma lista não vazia.")
    if len(itens) > MAX_ITENS_EVIDENCIA:
        raise OutputValidationError("evidence excede o número de itens permitido.")
    evidencia = tuple(_texto_saida(item, "evidence")[:MAX_EVIDENCIA] for item in itens)
    aprovado = dados.get("approved", False)
    if not isinstance(aprovado, bool):
        raise OutputValidationError("approved tem de ser booleano.")
    return AgentOutput(
        summary=resumo,
        evidence=evidencia,
        approval_claim=aprovado,
    )
