from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from agents.definitions import AgentDefinition, parse_agent_definition
from agents.runner import AgentRunner, RunnerConfig
from approvals.tokens import ApprovalToken, SolicitacaoAprovacao, TokenStore
from workflows.create import (
    PASSOS,
    AprovacaoInvalida,
    CheckpointStore,
    CreateRequest,
    CreateWorkflow,
    FluxoInativo,
    Step,
    WorkflowDependencies,
    hash_token,
)

from app.core.config import Settings, load_settings
from app.core.events import Event, EventBus
from app.core.tasks import SqliteTaskStore, TaskStatus
from app.llm.contracts import ModelRequest, ModelResponse, ProviderKind

TASK_ID = "task-criar-1"
CORRELATION_ID = "corr-criar-1"
DIFF_HASH = "a" * 64
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765
TIMEOUT_S = 5
TOTAL_PASSOS_AGENTE = 6

CHAVES: dict[str, str] = {passo.value: f"chave-{passo.value}" for passo in PASSOS}

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


def _resposta(resumo: str, aprovado: bool | None = None) -> str:
    dados: dict[str, object] = {"summary": resumo, "evidence": ["evidencia.md"]}
    if aprovado is not None:
        dados["approved"] = aprovado
    return json.dumps(dados)


def _respostas(aprovado: bool | None = None) -> list[str]:
    return [_resposta(f"resultado {passo.value}", aprovado) for passo in PASSOS]


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


def _settings(
    tmp_path: Path, *, create_flow: bool = True, ui_ativa: bool = True
) -> Settings:
    base = tmp_path / "project"
    base.mkdir(exist_ok=True)
    return load_settings(
        {
            "HCW_CREATE_FLOW": "true" if create_flow else "false",
            "HCW_UI_ENABLED": "true" if ui_ativa else "false",
            "HCW_UI_TOKEN": TOKEN_FALSO if ui_ativa else "",
        },
        base_dir=base,
    )


def _dependencias(
    tmp_path: Path,
    provider: FakeProvider,
    sink: RecordingSink,
    *,
    create_flow: bool = True,
    ui_ativa: bool = True,
) -> tuple[Settings, WorkflowDependencies, TokenStore]:
    settings = _settings(tmp_path, create_flow=create_flow, ui_ativa=ui_ativa)
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
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")
    tarefas.initialize()
    deps = WorkflowDependencies(
        settings=settings,
        tasks=tarefas,
        checkpoints=CheckpointStore(tmp_path / "checkpoints.sqlite3"),
        events=EventBus([sink]),
        runner=runner,
        tokens=TokenStore(settings),
    )
    return settings, deps, deps.tokens


def _emitir_token(
    tokens: TokenStore, *, correlation_id: str = CORRELATION_ID
) -> ApprovalToken:
    return tokens.emitir(
        SolicitacaoAprovacao(
            task_id=TASK_ID,
            correlation_id=correlation_id,
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
    correlation_id: str = CORRELATION_ID,
) -> CreateRequest:
    return CreateRequest(
        task_id=TASK_ID,
        correlation_id=correlation_id,
        pedido="Criar funcionalidade de teste",
        diff_hash=DIFF_HASH,
        token_aprovacao=token_aprovacao,
        chaves=CHAVES if chaves is None else chaves,
    )


def _eventos_criacao(sink: RecordingSink) -> list[str]:
    return [evento.kind for evento in sink.eventos if evento.kind.startswith("create.")]


def test_fluxo_percorre_todos_os_passos_e_usa_aprovacao_da_ui(
    tmp_path: Path,
) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas())
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)
    token = _emitir_token(tokens)
    fluxo = CreateWorkflow(deps)

    parcial = fluxo.executar(_pedido())

    assert parcial.aguardando_aprovacao is True
    assert parcial.last_completed_step is Step.ARQUITECTURA

    completo = fluxo.executar(_pedido(token.token))

    assert completo.status is TaskStatus.COMPLETED
    assert completo.last_completed_step is Step.RELATORIO
    assert completo.aguardando_aprovacao is False
    assert _eventos_criacao(sink) == [f"create.{passo.value}" for passo in PASSOS]
    assert len(provider.pedidos) == TOTAL_PASSOS_AGENTE
    assert completo.checkpoint.pending_token_hash == hash_token(token.token)
    assert token.token not in repr(completo.checkpoint)


def test_aprovacao_reivindicada_pelo_modelo_nao_avanca_sem_token(
    tmp_path: Path,
) -> None:
    sink = RecordingSink()
    provider = FakeProvider([_resposta("resultado", True) for _ in range(3)])
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)

    resultado = CreateWorkflow(deps).executar(_pedido())

    assert resultado.aguardando_aprovacao is True
    assert resultado.last_completed_step is Step.ARQUITECTURA
    assert "create.aprovacao" not in _eventos_criacao(sink)
    assert tokens.quantidade == 0


def test_chave_repetida_nao_duplica_eventos_nem_avanca_estado(
    tmp_path: Path,
) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas())
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)
    token = _emitir_token(tokens)
    pedido = _pedido(token.token)
    fluxo = CreateWorkflow(deps)
    primeiro = fluxo.executar(pedido)
    eventos = _eventos_criacao(sink)
    chamadas = len(provider.pedidos)
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")

    segundo = fluxo.executar(pedido)

    assert _eventos_criacao(sink) == eventos
    assert len(provider.pedidos) == chamadas
    assert segundo.checkpoint == primeiro.checkpoint
    tarefa = tarefas.get(TASK_ID)
    assert tarefa is not None
    assert tarefa.status is TaskStatus.COMPLETED


def test_token_com_correlacao_diferente_e_recusado(tmp_path: Path) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas())
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)
    token = _emitir_token(tokens, correlation_id="outra-correlacao")

    with pytest.raises(AprovacaoInvalida):
        CreateWorkflow(deps).executar(_pedido(token.token))

    assert "create.aprovacao" not in _eventos_criacao(sink)
    checkpoint = deps.checkpoints.get(TASK_ID)
    assert checkpoint is not None
    assert checkpoint.last_completed_step is Step.ARQUITECTURA


def test_fluxo_inativo_recusa_execucao(tmp_path: Path) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas())
    _settings_obj, deps, _tokens = _dependencias(
        tmp_path, provider, sink, create_flow=False
    )

    with pytest.raises(FluxoInativo):
        CreateWorkflow(deps).executar(_pedido())

    assert sink.eventos == []


def test_status_da_tarefa_segue_o_checkpoint(tmp_path: Path) -> None:
    sink = RecordingSink()
    provider = FakeProvider(_respostas())
    _settings_obj, deps, tokens = _dependencias(tmp_path, provider, sink)
    token = _emitir_token(tokens)
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")
    fluxo = CreateWorkflow(deps)

    parcial = fluxo.executar(_pedido())
    completo = fluxo.executar(_pedido(token.token))

    assert parcial.status is TaskStatus.RUNNING
    assert completo.status is TaskStatus.COMPLETED
    tarefa = tarefas.get(TASK_ID)
    assert tarefa is not None and tarefa.status is TaskStatus.COMPLETED
