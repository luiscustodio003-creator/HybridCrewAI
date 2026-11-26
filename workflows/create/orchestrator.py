"""Orquestração determinística do fluxo CREATE com checkpoints verificáveis."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hmac import compare_digest

from agents.runner import AgentRun, AgentRunner, ApprovalState
from approvals.tokens import TokenStore
from workflows.create.models import (
    PASSOS,
    AprovacaoInvalida,
    Checkpoint,
    CreateRequest,
    EtapaFalhou,
    FluxoInativo,
    Step,
    WorkflowError,
    WorkflowResult,
    hash_token,
)
from workflows.create.state import CheckpointStore

from app.core.config import Settings
from app.core.events import EventBus, EventContext, new_event
from app.core.logging import bind_context, reset_context
from app.core.results import ToolStatus
from app.core.tasks import (
    SqliteTaskStore,
    Task,
    TaskSpec,
    TaskStatus,
    new_task,
    transitar,
    utc_now,
)

AGENTE_WORKFLOW = "workflow-create"
AGENTES_POR_PASSO: dict[Step, str] = {
    Step.REQUISITOS: "planeador",
    Step.PLANO: "planeador",
    Step.ARQUITECTURA: "arquitecto",
    Step.EXECUCAO: "implementador",
    Step.REVISAO: "revisor",
    Step.RELATORIO: "relator",
}


@dataclass(frozen=True, slots=True)
class WorkflowDependencies:
    """Dependências explícitas e injectadas da orquestração."""

    settings: Settings
    tasks: SqliteTaskStore
    checkpoints: CheckpointStore
    events: EventBus
    runner: AgentRunner
    tokens: TokenStore


class CreateWorkflow:
    """Executa e retoma o fluxo CREATE sem confiar em texto do modelo."""

    def __init__(self, deps: WorkflowDependencies) -> None:
        """Valida as dependências da orquestração."""
        if not isinstance(deps, WorkflowDependencies):
            raise WorkflowError("deps tem de ser WorkflowDependencies.")
        self._deps = deps

    def executar(self, pedido: CreateRequest) -> WorkflowResult:
        """Executa os passos pendentes ou devolve o resultado já confirmado."""
        if not isinstance(pedido, CreateRequest):
            raise WorkflowError("pedido tem de ser CreateRequest.")
        if not self._deps.settings.create_flow:
            raise FluxoInativo("O fluxo CREATE está desactivado na configuração.")
        contexto = EventContext(
            correlation_id=pedido.correlation_id,
            task_id=pedido.task_id,
            agent=AGENTE_WORKFLOW,
            phase="create",
        )
        marcador = bind_context(contexto)
        try:
            return self._executar(pedido, contexto)
        finally:
            reset_context(marcador)

    def _executar(
        self, pedido: CreateRequest, contexto: EventContext
    ) -> WorkflowResult:
        checkpoint = self._preparar_tarefa(pedido)
        evidencias: list[str] = []
        for passo in PASSOS:
            if self._aguarda_aprovacao(pedido, checkpoint, passo):
                return WorkflowResult(
                    task_id=pedido.task_id,
                    correlation_id=pedido.correlation_id,
                    checkpoint=checkpoint,
                    aguardando_aprovacao=True,
                    evidencias=tuple(evidencias),
                )
            if self._deps.checkpoints.ja_registrada(
                pedido.task_id, passo, pedido.chave_para(passo)
            ):
                continue
            checkpoint, novas = self._executar_passo(
                pedido, checkpoint, passo, contexto
            )
            evidencias.extend(novas)
            self._deps.checkpoints.save(checkpoint)
            self._deps.checkpoints.registrar_chave(
                pedido.task_id, passo, pedido.chave_para(passo)
            )
        return self._concluir(pedido, checkpoint, evidencias)

    def _aguarda_aprovacao(
        self, pedido: CreateRequest, checkpoint: Checkpoint, passo: Step
    ) -> bool:
        """Indica se o fluxo deve parar antes de pedir o token da UI."""
        estado = (passo, pedido.token_aprovacao, checkpoint.pending_token_hash)
        return estado == (Step.APROVACAO, None, None)

    def _executar_passo(
        self,
        pedido: CreateRequest,
        checkpoint: Checkpoint,
        passo: Step,
        contexto: EventContext,
    ) -> tuple[Checkpoint, tuple[str, ...]]:
        """Executa um passo confirmado e devolve o novo checkpoint."""
        if passo is Step.APROVACAO:
            return self._aprovar(pedido, checkpoint, passo, contexto), ()
        if passo is Step.PEDIDO:
            return self._registrar_pedido(pedido, checkpoint, passo, contexto), ()
        return self._executar_agente(pedido, checkpoint, passo, contexto)

    def _preparar_tarefa(self, pedido: CreateRequest) -> Checkpoint:
        """Cria a tarefa e o checkpoint inicial quando ainda não existem."""
        checkpoint = self._deps.checkpoints.get(pedido.task_id)
        if checkpoint is not None:
            return checkpoint
        tarefa = self._deps.tasks.get(pedido.task_id)
        if tarefa is None:
            especificacao = TaskSpec(
                title=f"Fluxo CREATE: {pedido.task_id}",
                description=pedido.pedido[:500],
                agent=AGENTE_WORKFLOW,
                phase="create",
                chave=f"create:{pedido.task_id}",
            )
            tarefa = replace(new_task(especificacao), task_id=pedido.task_id)
        tarefa = self._garantir_running(tarefa)
        self._deps.tasks.save(tarefa)
        checkpoint = Checkpoint(
            task_id=pedido.task_id,
            correlation_id=pedido.correlation_id,
            status=TaskStatus.RUNNING,
            last_completed_step=None,
            pending_token_hash=None,
            agent=AGENTE_WORKFLOW,
            phase="create",
            updated_at=utc_now(),
        )
        self._deps.checkpoints.save(checkpoint)
        return checkpoint

    def _garantir_running(self, tarefa: Task) -> Task:
        """Faz a transição mínima para RUNNING sem repetir estados."""
        if tarefa.status is TaskStatus.CREATED:
            tarefa = transitar(tarefa, TaskStatus.QUEUED)
        if tarefa.status is TaskStatus.QUEUED:
            tarefa = transitar(tarefa, TaskStatus.RUNNING)
        return tarefa

    def _registrar_pedido(
        self,
        pedido: CreateRequest,
        checkpoint: Checkpoint,
        passo: Step,
        contexto: EventContext,
    ) -> Checkpoint:
        """Regista o pedido como primeiro passo verificável."""
        self._publicar(passo, AGENTE_WORKFLOW, pedido, contexto)
        return self._avancar(checkpoint, passo, AGENTE_WORKFLOW)

    def _aprovar(
        self,
        pedido: CreateRequest,
        checkpoint: Checkpoint,
        passo: Step,
        contexto: EventContext,
    ) -> Checkpoint:
        """Valida o token emitido pela UI e guarda apenas o digest."""
        if pedido.token_aprovacao is None:
            raise AprovacaoInvalida("Token de aprovação em falta.")
        aprovacao = self._deps.tokens.validar(
            pedido.token_aprovacao, pedido.task_id, pedido.diff_hash
        )
        if not compare_digest(aprovacao.correlation_id, pedido.correlation_id):
            raise AprovacaoInvalida("O token de aprovação pertence a outra correlação.")
        digest = hash_token(pedido.token_aprovacao)
        self._publicar(passo, AGENTE_WORKFLOW, pedido, contexto)
        return self._avancar(
            checkpoint, passo, AGENTE_WORKFLOW, pending_token_hash=digest
        )

    def _executar_agente(
        self,
        pedido: CreateRequest,
        checkpoint: Checkpoint,
        passo: Step,
        contexto: EventContext,
    ) -> tuple[Checkpoint, tuple[str, ...]]:
        """Executa um agente local e aceita apenas ToolResult DONE."""
        agente = AGENTES_POR_PASSO[passo]
        estado = (
            ApprovalState.APROVADO
            if passo in (Step.EXECUCAO, Step.REVISAO, Step.RELATORIO)
            else ApprovalState.PENDENTE
        )
        resultado = self._deps.runner.executar(
            AgentRun(
                agent_id=agente,
                task_id=pedido.task_id,
                correlation_id=pedido.correlation_id,
                phase="create",
                untrusted={"pedido": pedido.pedido, "etapa": passo.value},
                approval_state=estado,
            )
        )
        if resultado.status is not ToolStatus.DONE:
            raise EtapaFalhou(f"Passo {passo.value} falhou: {resultado.error}.")
        self._publicar(passo, agente, pedido, contexto)
        return self._avancar(checkpoint, passo, agente), tuple(resultado.evidence)

    def _publicar(
        self,
        passo: Step,
        agente: str,
        pedido: CreateRequest,
        contexto: EventContext,
    ) -> None:
        """Publica o evento verificável de um passo concluído."""
        local = replace(contexto, agent=agente)
        self._deps.events.publish(
            new_event(
                local,
                kind=f"create.{passo.value}",
                message=f"Passo {passo.value} concluído.",
                data={
                    "step": passo.value,
                    "idempotency_key": pedido.chave_para(passo),
                },
            )
        )

    def _avancar(
        self,
        checkpoint: Checkpoint,
        passo: Step,
        agente: str,
        pending_token_hash: str | None = None,
    ) -> Checkpoint:
        """Devolve um checkpoint actualizado após um passo confirmado."""
        pendente = (
            pending_token_hash
            if pending_token_hash is not None
            else checkpoint.pending_token_hash
        )
        return replace(
            checkpoint,
            status=TaskStatus.RUNNING,
            last_completed_step=passo,
            pending_token_hash=pendente,
            agent=agente,
            version=checkpoint.version + 1,
            updated_at=utc_now(),
        )

    def _concluir(
        self, pedido: CreateRequest, checkpoint: Checkpoint, evidencias: list[str]
    ) -> WorkflowResult:
        """Marca a tarefa como concluída quando todos os passos estão firmes."""
        tarefa = self._deps.tasks.get(pedido.task_id)
        if tarefa is not None and tarefa.status is not TaskStatus.COMPLETED:
            self._deps.tasks.save(transitar(tarefa, TaskStatus.COMPLETED))
            checkpoint = replace(
                checkpoint,
                status=TaskStatus.COMPLETED,
                version=checkpoint.version + 1,
                updated_at=utc_now(),
            )
            self._deps.checkpoints.save(checkpoint)
        return WorkflowResult(
            task_id=pedido.task_id,
            correlation_id=pedido.correlation_id,
            checkpoint=checkpoint,
            aguardando_aprovacao=False,
            evidencias=tuple(evidencias),
        )
