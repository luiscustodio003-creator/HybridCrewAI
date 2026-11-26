"""Casos de referência determinísticos para a avaliação da Fase 4."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from agents.runner import AgentRun, ApprovalState, parse_agent_output
from approvals.tokens import DiffAlterado, TarefaInvalida
from execution import ExecutionRequest, ExecutionResult, SimpleRunner
from tests.eval.scorer import (
    CASO_DOURADO_ID,
    INDICE_TOKEN_HASH,
    PASSOS_APOS_APROVACAO,
    PASSOS_ATE_APROVACAO,
    PASSOS_RESTANTES,
    TIMEOUT_S,
    Case,
    CaseResult,
    _checar,
    _diff_alterado,
    _recusado,
    _token_de_outra_tarefa,
)
from tests.integration.test_create_golden import (
    DIFF_HASH as DIFF_HASH_DOURADO,
)
from tests.integration.test_create_golden import (
    RELATORIO as RELATORIO_DOURADO,
)
from tests.integration.test_create_golden import (
    test_caso_dourado_calculadora_ponta_a_ponta,
)
from tests.integration.test_create_workflow_checkpoint import (
    CORRELATION_ID,
    DIFF_HASH,
    TASK_ID,
    FakeProvider,
    RecordingSink,
    _dependencias,
    _emitir_token,
    _eventos_criacao,
    _pedido,
    _respostas,
)
from tests.unit.test_agent_runner import RecordingSink as AgenteSink
from tests.unit.test_agent_runner import _resposta, _run, _runner
from workflows.create import (
    PASSOS,
    CreateWorkflow,
    Step,
    WorkflowDependencies,
    hash_token,
)

from app.core.events import EventBus
from app.core.results import ToolStatus
from app.core.tasks import TaskStatus
from app.llm.egress import FIM


def _token_hash_dourado() -> str:
    for linha in RELATORIO_DOURADO.read_text(encoding="utf-8").splitlines():
        if "| `token_hash` |" in linha:
            partes = linha.split("`")
            return partes[INDICE_TOKEN_HASH] if len(partes) > INDICE_TOKEN_HASH else ""
    return ""


def _caso_dourado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CaseResult:
    capturados: list[ExecutionResult] = []
    original = SimpleRunner.executar

    def capturar(self: SimpleRunner, pedido: ExecutionRequest) -> ExecutionResult:
        resultado = original(self, pedido)
        capturados.append(resultado)
        return resultado

    monkeypatch.setattr(SimpleRunner, "executar", capturar)
    test_caso_dourado_calculadora_ponta_a_ponta(tmp_path, monkeypatch)
    stdout = next(
        (
            item.split("=", 1)[1]
            for item in capturados[0].tool_result.evidence
            if item.startswith("stdout_sha256=")
        ),
        "",
    )
    relatorio = RELATORIO_DOURADO.read_bytes()
    evidencias = (
        f"diff_hash={DIFF_HASH_DOURADO}",
        f"token_hash={_token_hash_dourado()}",
        f"stdout_sha256={stdout}",
        f"relatorio_sha256={hashlib.sha256(relatorio).hexdigest()}",
    )
    verificacoes = (
        _checar("fluxo ponta a ponta", True),
        _checar(
            "execução capturada",
            len(capturados) == 1,
            f"{len(capturados)} execuções",
        ),
    )
    return CaseResult(CASO_DOURADO_ID, verificacoes, evidencias)


def _executor_recusa(deps: WorkflowDependencies) -> bool:
    destino = RecordingSink()
    executor = SimpleRunner(deps.settings, deps.tokens, EventBus([destino]))
    resultado = executor.executar(
        ExecutionRequest(
            task_id=TASK_ID,
            correlation_id=CORRELATION_ID,
            diff_hash=DIFF_HASH,
            approval_token="token-invalido-evidencia",
            command=(sys.executable, "-c", "pass"),
            timeout_s=TIMEOUT_S,
        )
    )
    return (
        resultado.tool_result.status is ToolStatus.FAILED
        and resultado.workspace is None
        and any(item.kind == "execution.recusado" for item in destino.eventos)
    )


def _caso_aprovacao_obrigatoria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> CaseResult:
    destino = RecordingSink()
    _settings, deps, tokens = _dependencias(
        tmp_path, FakeProvider(_respostas(PASSOS_ATE_APROVACAO)), destino
    )
    fluxo = CreateWorkflow(deps)
    parado = fluxo.executar(_pedido())
    token = _emitir_token(tokens)
    verificacoes = (
        _checar(
            "paragem antes da aprovação",
            parado.aguardando_aprovacao
            and parado.checkpoint.last_completed_step is Step.ARQUITECTURA,
        ),
        _checar(
            "token de outra tarefa recusado",
            _recusado(
                lambda: fluxo.executar(_pedido(_token_de_outra_tarefa(tokens))),
                TarefaInvalida,
            ),
        ),
        _checar(
            "diff alterado recusado",
            _recusado(
                lambda: fluxo.executar(_diff_alterado(token.token)), DiffAlterado
            ),
        ),
        _checar("executor recusa sem token válido", _executor_recusa(deps)),
    )
    passo_parado = parado.checkpoint.last_completed_step
    evidencias = (
        f"checkpoint={passo_parado.value if passo_parado is not None else ''}",
    )
    return CaseResult("aprovacao_obrigatoria", verificacoes, evidencias)


def _caso_claim_nao_aprova(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> CaseResult:
    destino = AgenteSink()
    runner, _provider = _runner([_resposta(aprovado=True)], sink=destino)
    run: AgentRun = _run()
    resultado = runner.executar(run)
    saida = parse_agent_output(_resposta(aprovado=True))
    verificacoes = (
        _checar("claim observado na saída", saida.approval_claim),
        _checar(
            "estado continua pendente", run.approval_state is ApprovalState.PENDENTE
        ),
        _checar(
            "sem evento de aprovação",
            not any("aprovacao" in item.kind for item in destino.eventos),
        ),
        _checar("resultado DONE", resultado.status is ToolStatus.DONE),
    )
    return CaseResult("approved_claim_nao_aprova", verificacoes)


def _caso_saida_invalida(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CaseResult:
    primeiro_destino = AgenteSink()
    runner, _provider = _runner(
        ["texto livre", _resposta()], sink=primeiro_destino, max_retries=1
    )
    resultado = runner.executar(_run())
    repeticoes = sum(
        item.kind == "agente.repeticao" for item in primeiro_destino.eventos
    )
    segundo_destino = AgenteSink()
    forjado, _outro = _runner(
        [json.dumps({"summary": "Plano", "evidence": [FIM]})], sink=segundo_destino
    )
    recusado = forjado.executar(_run())
    verificacoes = (
        _checar("repetição única", repeticoes == 1, f"{repeticoes} repetições"),
        _checar("resultado final DONE", resultado.status is ToolStatus.DONE),
        _checar("marcador forjado recusado", recusado.status is ToolStatus.FAILED),
        _checar(
            "sem repetição no marcador",
            not any(
                item.kind == "agente.repeticao" for item in segundo_destino.eventos
            ),
        ),
    )
    return CaseResult("saida_invalida_limitada", verificacoes)


def _caso_retomada(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CaseResult:
    primeiro_destino = RecordingSink()
    _settings, primeiro_deps, tokens = _dependencias(
        tmp_path, FakeProvider(_respostas(PASSOS_ATE_APROVACAO)), primeiro_destino
    )
    CreateWorkflow(primeiro_deps).executar(_pedido())
    token = _emitir_token(tokens)
    segundo_destino = RecordingSink()
    segundo_provider = FakeProvider(_respostas(PASSOS_APOS_APROVACAO))
    _settings, segundo_deps, _tokens = _dependencias(
        tmp_path, segundo_provider, segundo_destino, tokens=tokens
    )
    retomado = CreateWorkflow(segundo_deps).executar(_pedido(token.token))
    eventos = _eventos_criacao(segundo_destino)
    esperados = [
        f"create.{passo.value}" for passo in PASSOS[PASSOS.index(Step.APROVACAO) :]
    ]
    verificacoes = (
        _checar("retoma concluída", retomado.status is TaskStatus.COMPLETED),
        _checar(
            "último passo RELATORIO", retomado.last_completed_step is Step.RELATORIO
        ),
        _checar(
            "chamadas restantes", len(segundo_provider.pedidos) == PASSOS_RESTANTES
        ),
        _checar("eventos encadeados", eventos == esperados),
        _checar(
            "hash do token persistido",
            retomado.checkpoint.pending_token_hash == hash_token(token.token),
        ),
    )
    evidencias = (
        f"token_hash={hash_token(token.token)}",
        f"eventos_apos_aprovacao={len(eventos)}",
    )
    return CaseResult("retomada_idempotente", verificacoes, evidencias)


CASES: tuple[Case, ...] = (
    Case(CASO_DOURADO_ID, "Calculadora ponta a ponta", True, _caso_dourado),
    Case(
        "aprovacao_obrigatoria",
        "Aprovação só por token válido",
        False,
        _caso_aprovacao_obrigatoria,
    ),
    Case(
        "approved_claim_nao_aprova",
        "Claim do modelo não aprova",
        False,
        _caso_claim_nao_aprova,
    ),
    Case(
        "saida_invalida_limitada",
        "Saída inválida com limites",
        False,
        _caso_saida_invalida,
    ),
    Case(
        "retomada_idempotente",
        "Retoma sem repetir passos",
        False,
        _caso_retomada,
    ),
)
