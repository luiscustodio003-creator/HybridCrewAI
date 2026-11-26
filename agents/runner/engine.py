"""Execução determinística de um agente com resultado verificável."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from agents.definitions import AgentDefinition
from agents.definitions.prompt import render_prompt
from agents.runner.loader import load_runner_definitions, obter_definicao
from agents.runner.models import (
    AgentRun,
    AgentRunError,
    ApprovalState,
    ForgedMarkerError,
    OutputValidationError,
    RunnerConfig,
    parse_agent_output,
)
from app.core.events import Event, EventContext, EventLevel, EventSink, new_event
from app.core.results import ToolResult, ToolStatus, new_tool_result
from app.llm.contracts import ModelRequest, ModelResponse, ProviderError


class ModelProvider(Protocol):
    """Porta mínima usada pelo runner; nenhuma rede é iniciada aqui."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Devolve uma resposta normalizada."""
        ...


class AgentRunner:
    """Executa definições locais sem interpretar texto do modelo como comando."""

    __slots__ = (
        "_config",
        "_definitions",
        "_event_sink",
        "_provider",
    )

    def __init__(
        self,
        provider: ModelProvider,
        config: RunnerConfig,
        definitions: Mapping[str, AgentDefinition] | None = None,
        event_sink: EventSink | None = None,
    ) -> None:
        """Valida a configuração e guarda apenas dados imutáveis."""
        if not callable(getattr(provider, "complete", None)):
            raise AgentRunError("provider tem de implementar complete.")
        if not isinstance(config, RunnerConfig):
            raise AgentRunError("config tem de ser RunnerConfig.")
        if definitions is None:
            definicoes = load_runner_definitions()
        elif isinstance(definitions, Mapping):
            definicoes = dict(definitions)
        else:
            raise AgentRunError("definicoes tem de ser um mapping.")
        for identificador, definicao in definicoes.items():
            if not isinstance(identificador, str) or not isinstance(
                definicao, AgentDefinition
            ):
                raise AgentRunError("definicoes inválidas.")
        if event_sink is not None and not callable(getattr(event_sink, "write", None)):
            raise AgentRunError("event_sink tem de implementar write.")
        self._provider = provider
        self._config = config
        self._definitions = definicoes
        self._event_sink = event_sink

    def executar(self, run: AgentRun) -> ToolResult:
        """Executa o agente e devolve sempre um ToolResult verificado."""
        if not isinstance(run, AgentRun):
            raise AgentRunError("run tem de ser AgentRun.")
        contexto = EventContext(
            correlation_id=run.correlation_id,
            task_id=run.task_id,
            agent=run.agent_id,
            phase=run.phase,
        )
        inicio = new_event(
            contexto,
            kind="agente.iniciado",
            message=f"Agente {run.agent_id} iniciado.",
            data={
                "approval_state": run.approval_state.value,
                "max_retries": self._config.max_retries,
            },
        )
        if not self._publicar(inicio):
            return self._falhar(
                contexto, "falha ao publicar evento de início", run.approval_state
            )
        preparado = self._preparar(run, contexto)
        if isinstance(preparado, ToolResult):
            return preparado
        definicao, prompt = preparado
        return self._executar_tentativas(run, contexto, definicao, prompt)

    def _preparar(
        self,
        run: AgentRun,
        contexto: EventContext,
    ) -> tuple[AgentDefinition, str] | ToolResult:
        try:
            definicao = obter_definicao(self._definitions, run.agent_id)
        except AgentRunError as erro:
            return self._falhar(contexto, str(erro), run.approval_state)
        return definicao, render_prompt(definicao, run.untrusted)

    def _executar_tentativas(
        self,
        run: AgentRun,
        contexto: EventContext,
        definicao: AgentDefinition,
        prompt: str,
    ) -> ToolResult:
        total = self._config.max_retries + 1
        tentativa = 1
        while True:
            pedido = ModelRequest(
                provider=self._config.provider_kind,
                model=self._config.model,
                prompt=prompt,
                timeout_s=self._config.timeout_s,
                task_id=run.task_id,
                correlation_id=run.correlation_id,
            )
            try:
                resposta = self._provider.complete(pedido)
                saida = parse_agent_output(resposta.text)
            except ProviderError as erro:
                return self._falhar(
                    contexto,
                    f"fornecedor {erro.kind.value}: {erro}",
                    run.approval_state,
                )
            except ForgedMarkerError as erro:
                return self._falhar(
                    contexto,
                    f"marcador forjado na saida invalida: {erro}",
                    run.approval_state,
                )
            except OutputValidationError as erro:
                if tentativa >= total:
                    return self._falhar(
                        contexto,
                        f"saida invalida apos {total} tentativas",
                        run.approval_state,
                    )
                repeticao = new_event(
                    contexto,
                    kind="agente.repeticao",
                    message="Saída inválida; nova tentativa.",
                    level=EventLevel.WARNING,
                    data={
                        "approval_state": run.approval_state.value,
                        "tentativa": tentativa,
                        "motivo": str(erro),
                    },
                )
                self._publicar(repeticao)
                tentativa += 1
                continue
            except Exception:
                return self._falhar(
                    contexto, "falha inesperada no fornecedor", run.approval_state
                )
            conclusao = new_event(
                contexto,
                kind="agente.concluido",
                message=f"Agente {definicao.agent_id} concluído.",
                data={
                    "approval_state": run.approval_state.value,
                    "tentativas": tentativa,
                },
            )
            if not self._publicar(conclusao):
                return self._falhar(
                    contexto,
                    "falha ao publicar evento de conclusão",
                    run.approval_state,
                )
            return new_tool_result(
                ToolStatus.DONE,
                saida.summary,
                saida.evidence,
            )

    def _publicar(self, evento: Event) -> bool:
        if self._event_sink is None:
            return True
        try:
            self._event_sink.write(evento)
        except Exception:
            return False
        return True

    def _falhar(
        self,
        contexto: EventContext,
        erro: str,
        estado: ApprovalState = ApprovalState.PENDENTE,
    ) -> ToolResult:
        falha = new_event(
            contexto,
            kind="agente.falhou",
            message=erro,
            level=EventLevel.ERROR,
            data={"approval_state": estado.value},
        )
        self._publicar(falha)
        return new_tool_result(
            ToolStatus.FAILED,
            "Execução do agente falhou.",
            error=erro,
        )
