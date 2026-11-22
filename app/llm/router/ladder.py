"""Escada de modelos e matriz de fallback, carregada de ficheiro JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.llm.contracts import ProviderKind

CONFIG_VERSION = 1


class TaskKind(StrEnum):
    """Tipos de tarefa usados pela matriz de fallback."""

    LIGHT = "light"
    CODE = "code"


class StepAction(StrEnum):
    """Acção decidida para cada degrau da escada."""

    USE = "use"
    REQUIRE_AUTHORIZATION = "require_authorization"
    PAUSE = "pause"


class LadderError(ValueError):
    """Configuração de escada inválida; a mensagem indica como corrigi-la."""


@dataclass(frozen=True, slots=True)
class LadderStep:
    """Um modelo candidato, identificado por fornecedor e nome."""

    provider: ProviderKind
    model: str

    def __post_init__(self) -> None:
        if not isinstance(self.provider, ProviderKind):
            raise TypeError("provider tem de ser ProviderKind.")
        if not self.model.strip():
            raise LadderError("model não pode estar vazio.")


@dataclass(frozen=True, slots=True)
class Ladder:
    """Escadas por tipo de tarefa, sem dependência de fornecedores concretos."""

    steps: dict[TaskKind, tuple[LadderStep, ...]]

    def __post_init__(self) -> None:
        missing = [tipo.value for tipo in TaskKind if tipo not in self.steps]
        if missing:
            raise LadderError(f"escada sem degraus para: {', '.join(missing)}.")
        for tipo, degraus in self.steps.items():
            if not isinstance(tipo, TaskKind):
                raise TypeError("As chaves de steps têm de ser TaskKind.")
            if not degraus:
                raise LadderError(f"A escada {tipo.value} não pode estar vazia.")

    def for_task(self, task_kind: TaskKind) -> tuple[LadderStep, ...]:
        """Devolve os degraus do tipo de tarefa pedido."""
        if not isinstance(task_kind, TaskKind):
            raise TypeError("task_kind tem de ser TaskKind.")
        return self.steps[task_kind]

    def models(self, task_kind: TaskKind) -> tuple[str, ...]:
        """Devolve os nomes de modelos do tipo de tarefa pedido."""
        return tuple(degrau.model for degrau in self.for_task(task_kind))


@dataclass(frozen=True, slots=True)
class RouteStep:
    """Decisão de política para um degrau da escada."""

    step: LadderStep
    action: StepAction
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.action, StepAction):
            raise TypeError("action tem de ser StepAction.")
        if not self.reason.strip():
            raise LadderError("reason não pode estar vazio.")


def _text_field(valor: dict[str, object], chave: str, contexto: str) -> str:
    texto = valor.get(chave)
    if not isinstance(texto, str) or not texto.strip():
        raise LadderError(f"{contexto}.{chave} tem de ser texto não vazio.")
    return texto.strip()


def _parse_step(valor: object, contexto: str) -> LadderStep:
    if not isinstance(valor, dict):
        raise LadderError(f"{contexto} tem de ser um objecto JSON.")
    provider_texto = _text_field(valor, "provider", contexto)
    try:
        provider = ProviderKind(provider_texto)
    except ValueError as erro:
        permitidos = ", ".join(item.value for item in ProviderKind)
        raise LadderError(
            f"{contexto}.provider inválido {provider_texto!r}; use {permitidos}."
        ) from erro
    return LadderStep(provider=provider, model=_text_field(valor, "model", contexto))


def load_ladder(path: str | Path) -> Ladder:
    """Carrega e valida a escada a partir de um ficheiro JSON local."""
    conteudo = Path(path).read_text(encoding="utf-8")
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise LadderError(f"Configuração de escada inválida: {erro.msg}.") from erro
    if not isinstance(dados, dict):
        raise LadderError("A configuração da escada tem de ser um objecto JSON.")
    if dados.get("version") != CONFIG_VERSION:
        raise LadderError(
            f"version tem de ser {CONFIG_VERSION}; recebido {dados.get('version')!r}."
        )
    secoes = dados.get("ladders")
    if not isinstance(secoes, dict):
        raise LadderError("ladders tem de ser um objecto JSON com as escadas.")

    escadas: dict[TaskKind, tuple[LadderStep, ...]] = {}
    for tipo in TaskKind:
        brutos = secoes.get(tipo.value)
        if not isinstance(brutos, list) or not brutos:
            raise LadderError(f"ladders.{tipo.value} tem de ser uma lista não vazia.")
        degraus = tuple(
            _parse_step(bruto, f"ladders.{tipo.value}[{indice}]")
            for indice, bruto in enumerate(brutos)
        )
        vistos: set[tuple[ProviderKind, str]] = set()
        for degrau in degraus:
            chave = (degrau.provider, degrau.model)
            if chave in vistos:
                raise LadderError(
                    f"Degrau repetido em {tipo.value}: {degrau.provider.value}/{degrau.model}."
                )
            vistos.add(chave)
        escadas[tipo] = degraus
    return Ladder(steps=escadas)


def _is_gemini(provider: ProviderKind) -> bool:
    return provider in {ProviderKind.GEMINI_TEXT, ProviderKind.GEMINI_LIVE}


def _decidir_degrau(
    degrau: LadderStep,
    task_kind: TaskKind,
    origem: ProviderKind,
    external_cloud_authorized: bool,
) -> RouteStep:
    destino = degrau.provider
    if _is_gemini(origem) and _is_gemini(destino):
        return RouteStep(degrau, StepAction.USE, "Gemini para Gemini é automático.")
    if destino is ProviderKind.EXTERNAL:
        if external_cloud_authorized:
            acao, motivo = StepAction.USE, "Outro cloud autorizado explicitamente."
        else:
            acao, motivo = (
                StepAction.REQUIRE_AUTHORIZATION,
                "Gemini para outro cloud exige autorização explícita.",
            )
    elif destino in {ProviderKind.OLLAMA, ProviderKind.FAKE}:
        if task_kind is TaskKind.LIGHT:
            acao, motivo = StepAction.USE, "Ollama é permitido em tarefa leve."
        else:
            acao, motivo = (
                StepAction.PAUSE,
                "Gemini para Ollama em código pausa e pede decisão.",
            )
    elif external_cloud_authorized:
        acao, motivo = StepAction.USE, "Entrada em cloud autorizada explicitamente."
    else:
        acao, motivo = (
            StepAction.REQUIRE_AUTHORIZATION,
            "Saída da origem para cloud exige autorização explícita.",
        )
    return RouteStep(degrau, acao, motivo)


def plan_fallback(
    ladder: Ladder,
    task_kind: TaskKind,
    *,
    source_provider: ProviderKind = ProviderKind.GEMINI_TEXT,
    external_cloud_authorized: bool = False,
) -> tuple[RouteStep, ...]:
    """Aplica a matriz de fallback a todos os degraus da escada pedida."""
    if not isinstance(ladder, Ladder):
        raise TypeError("ladder tem de ser Ladder.")
    origem, autorizado = source_provider, external_cloud_authorized
    degraus = ladder.for_task(task_kind)
    return tuple(_decidir_degrau(d, task_kind, origem, autorizado) for d in degraus)
