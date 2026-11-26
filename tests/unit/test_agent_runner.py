from __future__ import annotations

import json
from collections.abc import Sequence

import pytest
from agents.definitions import parse_agent_definition
from agents.runner import (
    AgentRun,
    AgentRunner,
    ApprovalState,
    OutputValidationError,
    RunnerConfig,
    parse_agent_output,
)
from agents.runner.models import MAX_RETRIES_PERMITIDAS

from app.core.events import Event
from app.core.results import ToolStatus
from app.llm.contracts import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)
from app.llm.egress import FIM

TIMEOUT_S = 5
TOTAL_TENTATIVAS = MAX_RETRIES_PERMITIDAS + 1

DEFINICAO = """---
id: planeador
nome: Planeador
versao: 1
entrada: texto
saida: json
ferramentas: leitura
---
Devolve resumo e evidência em JSON.
"""


class RecordingSink:
    def __init__(self) -> None:
        self.eventos: list[Event] = []

    def write(self, event: Event) -> None:
        self.eventos.append(event)


class FakeProvider:
    provider = ProviderKind.FAKE

    def __init__(self, respostas: Sequence[str | Exception]) -> None:
        self._respostas = list(respostas)
        self.pedidos: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        self.pedidos.append(request)
        resposta = self._respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return ModelResponse(
            provider=self.provider,
            model=request.model,
            text=resposta,
            task_id=request.task_id,
            correlation_id=request.correlation_id,
            latency_ms=0,
        )


def _resposta(resumo: str = "Plano criado", aprovado: bool | None = None) -> str:
    dados: dict[str, object] = {"summary": resumo, "evidence": ["plano.md"]}
    if aprovado is not None:
        dados["approved"] = aprovado
    return json.dumps(dados)


def _runner(
    respostas: Sequence[str | Exception],
    *,
    sink: RecordingSink | None = None,
    max_retries: int = 2,
) -> tuple[AgentRunner, FakeProvider]:
    provider = FakeProvider(respostas)
    runner = AgentRunner(
        provider=provider,
        config=RunnerConfig(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
            timeout_s=TIMEOUT_S,
            max_retries=max_retries,
        ),
        definitions={"planeador": parse_agent_definition(DEFINICAO, "planeador.md")},
        event_sink=sink,
    )
    return runner, provider


def _run() -> AgentRun:
    return AgentRun(
        agent_id="planeador",
        task_id="task-1",
        correlation_id="corr-1",
        phase="create",
        untrusted={"codigo": "print(1)"},
    )


def test_executar_devolve_tool_result_com_evidencia_e_eventos() -> None:
    sink = RecordingSink()
    runner, provider = _runner([_resposta()], sink=sink)
    resultado = runner.executar(_run())

    assert resultado.status is ToolStatus.DONE
    assert resultado.evidence == ("plano.md",)
    assert len(provider.pedidos) == 1
    pedido = provider.pedidos[0]
    assert pedido.provider is ProviderKind.FAKE
    assert pedido.timeout_s == TIMEOUT_S
    assert pedido.task_id == "task-1"
    assert pedido.correlation_id == "corr-1"
    assert "Devolve resumo e evidência em JSON." in pedido.prompt
    assert [evento.kind for evento in sink.eventos] == [
        "agente.iniciado",
        "agente.concluido",
    ]
    for evento in sink.eventos:
        assert evento.correlation_id == "corr-1"
        assert evento.task_id == "task-1"
        assert evento.agent == "planeador"
        assert evento.phase == "create"


def test_saida_invalida_e_repetida_ate_duas_vezes_antes_de_failed() -> None:
    runner, provider = _runner(["texto livre", "texto livre", "texto livre"])
    resultado = runner.executar(_run())

    assert resultado.status is ToolStatus.FAILED
    assert resultado.error is not None
    assert "invalida" in resultado.error
    assert len(provider.pedidos) == TOTAL_TENTATIVAS


def test_saida_invalida_uma_vez_e_depois_valida() -> None:
    runner, provider = _runner(["texto livre", _resposta()])
    resultado = runner.executar(_run())

    assert resultado.status is ToolStatus.DONE
    assert len(provider.pedidos) == TOTAL_TENTATIVAS - 1


def test_aprovacao_reivindicada_pelo_modelo_nao_altera_estado() -> None:
    sink = RecordingSink()
    runner, _ = _runner([_resposta(aprovado=True)], sink=sink)
    run = AgentRun(
        agent_id="planeador",
        task_id="task-1",
        correlation_id="corr-1",
        phase="create",
        untrusted={},
        approval_state=ApprovalState.PENDENTE,
    )

    resultado = runner.executar(run)

    assert resultado.status is ToolStatus.DONE
    assert all(
        evento.data["approval_state"] == ApprovalState.PENDENTE.value
        for evento in sink.eventos
    )
    assert all("approved" not in evento.data for evento in sink.eventos)
    assert parse_agent_output(_resposta(aprovado=True)).approval_claim is True


def test_definicao_desconhecida_devolve_failed_sem_chamar_modelo() -> None:
    runner, provider = _runner([])
    run = AgentRun("desconhecido", "task-1", "corr-1", "create", {})

    resultado = runner.executar(run)

    assert resultado.status is ToolStatus.FAILED
    assert "desconhecido" in (resultado.error or "")
    assert provider.pedidos == []


def test_marcador_forjado_na_evidencia_e_recusado() -> None:
    dados = {"summary": "Plano", "evidence": [FIM]}
    runner, _ = _runner([json.dumps(dados)])
    resultado = runner.executar(_run())

    assert resultado.status is ToolStatus.FAILED
    assert "invalida" in (resultado.error or "")


def test_erro_do_fornecedor_vira_failed_sem_dados_sensiveis() -> None:
    erro = ProviderError(
        ProviderKind.FAKE,
        ErrorKind.TIMEOUT,
        "tempo esgotado",
        "task-1",
        "corr-1",
    )
    runner, _ = _runner([erro])
    resultado = runner.executar(_run())

    assert resultado.status is ToolStatus.FAILED
    assert resultado.error is not None
    assert "timeout" in resultado.error


def test_timeout_invalido_e_recusado_na_construcao() -> None:
    with pytest.raises(ValueError, match="timeout_s"):
        RunnerConfig(ProviderKind.FAKE, "fake-model", 0)


def test_numero_de_repeticoes_acima_do_limite_e_recusado() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        RunnerConfig(
            ProviderKind.FAKE,
            "fake-model",
            TIMEOUT_S,
            max_retries=MAX_RETRIES_PERMITIDAS + 1,
        )


def test_saida_com_chave_desconhecida_e_recusada() -> None:
    dados = {"summary": "Plano", "evidence": ["plano.md"], "command": "rm -rf /"}
    with pytest.raises(OutputValidationError, match="desconhecida"):
        parse_agent_output(json.dumps(dados))
