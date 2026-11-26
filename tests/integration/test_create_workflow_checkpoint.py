from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from agents.definitions import AgentDefinition, parse_agent_definition
from agents.runner import AgentRunner, RunnerConfig
from approvals.tokens import ApprovalToken, SolicitacaoAprovacao, TokenStore
from workflows.create import (
    PASSOS,
    CheckpointStore,
    CreateRequest,
    CreateWorkflow,
    EtapaFalhou,
    Step,
    WorkflowDependencies,
    hash_token,
)

from app.core.config import Settings, load_settings
from app.core.events import Event, EventBus
from app.core.tasks import SqliteTaskStore, TaskStatus
from app.llm.contracts import (
    ErrorKind,
    ModelRequest,
    ModelResponse,
    ProviderError,
    ProviderKind,
)

TASK_ID = "task-integracao-1"
CORRELATION_ID = "corr-integracao-1"
DIFF_HASH = "b" * 64
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765
TIMEOUT_S = 5
PASSOS_ATE_FALHA = 3
CHAMADAS_ATE_FALHA = 4
CHAMADAS_RETOMADAS = 3

CHAVES: dict[str, str] = {
    passo.value: f"idempotencia-{passo.value}" for passo in PASSOS
}

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


def _resposta(passo: Step) -> str:
    return json.dumps({"summary": f"concluido {passo.value}", "evidence": ["passo.md"]})


def _definicoes() -> dict[str, AgentDefinition]:
    identificadores = (
        "planeador",
        "arquitecto",
        "implementador",
        "revisor",
        "relator",
    )
    return {
        identificador: parse_agent_definition(
            DEFINICAO.replace("id: planeador", f"id: {identificador}"),
            f"{identificador}.md",
        )
        for identificador in identificadores
    }


def _settings(tmp_path: Path) -> Settings:
    base = tmp_path / "project"
    base.mkdir(exist_ok=True)
    return load_settings(
        {
            "HCW_CREATE_FLOW": "true",
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
        },
        base_dir=base,
    )


def _dependencias(
    tmp_path: Path,
    provider: FakeProvider,
    sink: RecordingSink,
    tokens: TokenStore | None = None,
) -> tuple[Settings, WorkflowDependencies, TokenStore]:
    settings = _settings(tmp_path)
    runner = AgentRunner(
        provider=provider,
        config=RunnerConfig(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
            timeout_s=TIMEOUT_S,
            max_retries=0,
        ),
        definitions=_definicoes(),
        event_sink=sink,
    )
    emissor = tokens or TokenStore(settings)
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")
    tarefas.initialize()
    deps = WorkflowDependencies(
        settings=settings,
        tasks=tarefas,
        checkpoints=CheckpointStore(tmp_path / "checkpoints.sqlite3"),
        events=EventBus([sink]),
        runner=runner,
        tokens=emissor,
    )
    return settings, deps, emissor


def _emitir_token(tokens: TokenStore) -> ApprovalToken:
    return tokens.emitir(
        SolicitacaoAprovacao(
            task_id=TASK_ID,
            correlation_id=CORRELATION_ID,
            diff_hash=DIFF_HASH,
            porta=PORTA,
            headers={
                "Origin": f"http://127.0.0.1:{PORTA}",
                "Authorization": f"Bearer {TOKEN_FALSO}",
                "Sec-Fetch-Site": "same-origin",
            },
        )
    )


def _pedido(
    token_aprovacao: str | None = None,
    *,
    chaves: Mapping[str, str] | None = None,
) -> CreateRequest:
    return CreateRequest(
        task_id=TASK_ID,
        correlation_id=CORRELATION_ID,
        pedido="Criar funcionalidade com reinício",
        diff_hash=DIFF_HASH,
        token_aprovacao=token_aprovacao,
        chaves=CHAVES if chaves is None else chaves,
    )


def _respostas(passos: Sequence[Step]) -> list[str]:
    return [_resposta(passo) for passo in passos]


def _eventos_criacao(sink: RecordingSink) -> list[str]:
    return [evento.kind for evento in sink.eventos if evento.kind.startswith("create.")]


def _falha_fornecedor() -> ProviderError:
    return ProviderError(
        ProviderKind.FAKE,
        ErrorKind.NETWORK,
        "Falha determinística de teste.",
        TASK_ID,
        CORRELATION_ID,
    )


def _linha_checkpoint(tmp_path: Path) -> sqlite3.Row:
    ligacao = sqlite3.connect(tmp_path / "checkpoints.sqlite3")
    ligacao.row_factory = sqlite3.Row
    try:
        linha = ligacao.execute(
            "SELECT * FROM create_checkpoints WHERE task_id = ?", (TASK_ID,)
        ).fetchone()
        assert linha is not None
        return linha
    finally:
        ligacao.close()


def test_checkpoint_guarda_campos_obrigatorios_sem_guardar_token(
    tmp_path: Path,
) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas(PASSOS))
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)
    token = _emitir_token(tokens)
    fluxo = CreateWorkflow(deps)

    fluxo.executar(_pedido())
    fluxo.executar(_pedido(token.token))
    linha = _linha_checkpoint(tmp_path)

    assert linha["task_id"] == TASK_ID
    assert linha["correlation_id"] == CORRELATION_ID
    assert linha["last_completed_step"] == Step.RELATORIO.value
    assert linha["pending_token_hash"] == hash_token(token.token)
    assert token.token not in " ".join(str(valor) for valor in linha)


def test_checkpoint_sobrevive_a_reinicio_sem_repetir_passos(tmp_path: Path) -> None:
    sink = RecordingSink()
    primeiro_provider = FakeProvider(_respostas(PASSOS))
    _settings_obj, primeiro_deps, tokens = _dependencias(
        tmp_path, primeiro_provider, sink
    )
    CreateWorkflow(primeiro_deps).executar(_pedido())
    token = _emitir_token(tokens)

    segundo_sink = RecordingSink()
    segundo_provider = FakeProvider(_respostas(PASSOS[5:]))
    _settings_obj, segundo_deps, _tokens = _dependencias(
        tmp_path, segundo_provider, segundo_sink, tokens=tokens
    )

    resultado = CreateWorkflow(segundo_deps).executar(_pedido(token.token))
    restantes = PASSOS[PASSOS.index(Step.APROVACAO) :]

    assert resultado.status is TaskStatus.COMPLETED
    assert resultado.last_completed_step is Step.RELATORIO
    assert len(segundo_provider.pedidos) == CHAMADAS_RETOMADAS
    assert _eventos_criacao(segundo_sink) == [
        f"create.{passo.value}" for passo in restantes
    ]


def test_retomada_reexecuta_apenas_passos_nao_confirmados(tmp_path: Path) -> None:
    sink = RecordingSink()
    ate_arquitectura = PASSOS[:PASSOS_ATE_FALHA]
    primeiro_provider = FakeProvider(
        [*_respostas(ate_arquitectura), _falha_fornecedor()]
    )
    _settings_obj, primeiro_deps, tokens = _dependencias(
        tmp_path, primeiro_provider, sink
    )
    token = _emitir_token(tokens)
    fluxo = CreateWorkflow(primeiro_deps)

    fluxo.executar(_pedido())

    with pytest.raises(EtapaFalhou):
        fluxo.executar(_pedido(token.token))

    checkpoint = primeiro_deps.checkpoints.get(TASK_ID)
    assert checkpoint is not None
    assert checkpoint.last_completed_step is Step.APROVACAO
    assert len(primeiro_provider.pedidos) == CHAMADAS_ATE_FALHA

    segundo_provider = FakeProvider(_respostas(PASSOS[5:]))
    segundo_sink = RecordingSink()
    _settings_obj, segundo_deps, _tokens = _dependencias(
        tmp_path, segundo_provider, segundo_sink, tokens=tokens
    )

    retomado = CreateWorkflow(segundo_deps).executar(_pedido(token.token))

    assert retomado.status is TaskStatus.COMPLETED
    assert retomado.last_completed_step is Step.RELATORIO
    assert [pedido.prompt for pedido in segundo_provider.pedidos]
    assert len(segundo_provider.pedidos) == CHAMADAS_RETOMADAS
    assert retomado.checkpoint.pending_token_hash == hash_token(token.token)
