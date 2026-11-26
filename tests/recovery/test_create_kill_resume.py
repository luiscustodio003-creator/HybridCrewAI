"""Recuperação e cancelamento reais do fluxo CREATE."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

import pytest
from tests.integration.test_create_workflow_checkpoint import TASK_ID as ID_TAREFA
from tests.integration.test_create_workflow_checkpoint import (
    FakeProvider,
    RecordingSink,
    _dependencias,
    _emitir_token,
    _eventos_criacao,
    _pedido,
    _respostas,
)
from workflows.create import (
    PASSOS,
    CheckpointStore,
    CheckpointStoreError,
    CreateWorkflow,
    Step,
)

from app.core.tasks import SqliteTaskStore, TaskStatus, transitar

RAIZ = Path(__file__).resolve().parents[2]
TOKEN_APROVACAO = "token-aprovacao-falso-16"
TIMEOUT_LEITURA = 30
TIMEOUT_PROCESSO = 10
PASSOS_AGENTE: tuple[Step, ...] = tuple(
    passo for passo in PASSOS if passo not in (Step.PEDIDO, Step.APROVACAO)
)
PASSOS_COM_EVENTO: tuple[Step, ...] = tuple(
    passo for passo in PASSOS if passo is not Step.PEDIDO
)

TRABALHADOR = """
import sys
import time
from pathlib import Path

sys.path.insert(0, sys.argv[1])

from approvals.tokens import store as modulo_tokens
from tests.integration.test_create_workflow_checkpoint import (
    RecordingSink,
    TASK_ID,
    _dependencias,
    _emitir_token,
    _pedido,
)
from workflows.create import CreateWorkflow
from app.llm.contracts import ModelResponse, ProviderKind

TOKEN = sys.argv[3]


class Bloqueador:
    provider = ProviderKind.FAKE

    def __init__(self):
        self._bloqueou = False

    def complete(self, request):
        if not self._bloqueou:
            self._bloqueou = True
            print("PRONTO:" + TASK_ID, flush=True)
            time.sleep(60)
        return ModelResponse(
            provider=self.provider,
            model=request.model,
            text='{"summary": "concluido", "evidence": ["passo.md"]}',
            task_id=request.task_id,
            correlation_id=request.correlation_id,
            latency_ms=0,
        )


modulo_tokens.secrets.token_urlsafe = lambda _tamanho: TOKEN
_settings, deps, tokens = _dependencias(
    Path(sys.argv[2]), Bloqueador(), RecordingSink()
)
aprovacao = _emitir_token(tokens)
CreateWorkflow(deps).executar(_pedido(aprovacao.token))
"""


def _registrar_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "approvals.tokens.store.secrets.token_urlsafe",
        lambda _tamanho: TOKEN_APROVACAO,
    )


def _iniciar_worker(tmp_path: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            TRABALHADOR,
            str(RAIZ),
            str(tmp_path),
            TOKEN_APROVACAO,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _esperar_pronto(processo: subprocess.Popen[str]) -> None:
    fila: Queue[str | None] = Queue()
    Thread(
        target=lambda: fila.put(
            processo.stdout.readline() if processo.stdout is not None else None
        ),
        daemon=True,
    ).start()
    try:
        linha = fila.get(timeout=TIMEOUT_LEITURA)
    except Empty:
        processo.kill()
        processo.communicate(timeout=TIMEOUT_PROCESSO)
        pytest.fail("O subprocesso do fluxo CREATE não sinalizou PRONTO.")
    assert linha is not None and linha.startswith(f"PRONTO:{ID_TAREFA}")


def _matar(processo: subprocess.Popen[str]) -> None:
    if processo.poll() is None:
        processo.kill()
    _, erro = processo.communicate(timeout=TIMEOUT_PROCESSO)
    assert "Traceback" not in erro


def _recuperar_sqlite(tmp_path: Path) -> None:
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")
    tarefas.initialize()
    checkpoints = CheckpointStore(tmp_path / "checkpoints.sqlite3")
    recuperadas = tarefas.recover_orphans()
    assert [tarefa.task_id for tarefa in recuperadas] == [ID_TAREFA]
    assert recuperadas[0].status is TaskStatus.INTERRUPTED
    interrompidos = checkpoints.recover_interrupted([ID_TAREFA])
    assert [checkpoint.task_id for checkpoint in interrompidos] == [ID_TAREFA]
    assert interrompidos[0].status is TaskStatus.INTERRUPTED
    tarefa = tarefas.get(ID_TAREFA)
    assert tarefa is not None
    tarefas.save(transitar(transitar(tarefa, TaskStatus.QUEUED), TaskStatus.RUNNING))


def test_kill_e_retoma_create_sem_repetir_passo_confirmado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Morte súbita mantém INTERRUPTED e a retoma não repete o pedido."""
    processo = _iniciar_worker(tmp_path)
    try:
        _esperar_pronto(processo)
    finally:
        _matar(processo)

    _recuperar_sqlite(tmp_path)
    _registrar_token(monkeypatch)
    sink = RecordingSink()
    provider = FakeProvider(_respostas(PASSOS_AGENTE))
    _settings, deps, tokens = _dependencias(tmp_path, provider, sink)
    aprovacao = _emitir_token(tokens)

    resultado = CreateWorkflow(deps).executar(_pedido(aprovacao.token))

    assert resultado.status is TaskStatus.COMPLETED
    assert resultado.last_completed_step is Step.RELATORIO
    assert len(provider.pedidos) == len(PASSOS_AGENTE)
    assert _eventos_criacao(sink) == [
        f"create.{passo.value}" for passo in PASSOS_COM_EVENTO
    ]


def test_cancelamento_impede_nova_execucao_com_sqlite_real(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Um fluxo cancelado não executa novos passos e fica CANCELLED no SQLite."""
    _registrar_token(monkeypatch)
    sink = RecordingSink()
    provider = FakeProvider(_respostas(PASSOS_AGENTE))
    _settings, deps, _tokens = _dependencias(tmp_path, provider, sink)
    fluxo = CreateWorkflow(deps)

    fluxo.executar(_pedido())
    cancelado = deps.checkpoints.cancelar(ID_TAREFA)
    tarefa = deps.tasks.get(ID_TAREFA)
    assert cancelado is not None and cancelado.status is TaskStatus.CANCELLED
    assert tarefa is not None
    deps.tasks.save(transitar(tarefa, TaskStatus.CANCELLED))
    chamadas = len(provider.pedidos)
    eventos = _eventos_criacao(sink)

    with pytest.raises(CheckpointStoreError, match="cancelado"):
        fluxo.executar(_pedido(TOKEN_APROVACAO))

    atual = deps.tasks.get(ID_TAREFA)
    assert atual is not None and atual.status is TaskStatus.CANCELLED
    assert len(provider.pedidos) == chamadas
    assert _eventos_criacao(sink) == eventos
