"""Testes unitários do executor simples com aprovação."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from approvals.tokens import SolicitacaoAprovacao, TokenStore
from execution import ExecutionRequest, SimpleRunner

from app.core.config import load_settings
from app.core.events import Event, EventBus
from app.core.results import ToolStatus

if TYPE_CHECKING:
    from app.core.config import Settings

HASH_DIFUSAO = "a" * 64
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765
TAREFA = "tarefa-execucao"
CORRELACAO = "correlacao-execucao"
LIMITE_SEGUNDOS = 4


class RecordingSink:
    """Destino em memória usado para verificar eventos emitidos."""

    def __init__(self) -> None:
        self.eventos: list[Event] = []

    def write(self, event: Event) -> None:
        """Guarda o evento recebido."""
        self.eventos.append(event)


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração isolada com token falso de teste."""
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {"HCW_UI_ENABLED": "true", "HCW_UI_TOKEN": TOKEN_FALSO},
        base_dir=base,
    )


def _token(
    store: TokenStore,
    *,
    task_id: str = TAREFA,
    correlation_id: str = CORRELACAO,
    diff_hash: str = HASH_DIFUSAO,
) -> str:
    """Emite um token autenticado para os parâmetros indicados."""
    solicitacao = SolicitacaoAprovacao(
        task_id=task_id,
        correlation_id=correlation_id,
        diff_hash=diff_hash,
        headers={
            "Authorization": f"Bearer {TOKEN_FALSO}",
            "Origin": f"http://127.0.0.1:{PORTA}",
        },
        porta=PORTA,
    )
    return store.emitir(solicitacao).token


def test_execucao_bem_sucedida_regista_isolated_false(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    sink = RecordingSink()
    runner = SimpleRunner(settings, store, EventBus([sink]))

    resultado = runner.executar(
        ExecutionRequest(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=HASH_DIFUSAO,
            approval_token=_token(store),
            command=(sys.executable, "-c", "print('ok')"),
            timeout_s=10,
        )
    )

    assert resultado.tool_result.status is ToolStatus.DONE
    assert resultado.isolated is False
    assert resultado.returncode == 0
    assert resultado.workspace is not None
    assert Path(resultado.workspace).is_relative_to(settings.data_dir)
    evento = next(e for e in sink.eventos if e.kind == "execution.concluido")
    assert evento.data["isolated"] is False
    assert evento.data["returncode"] == 0


def test_execucao_sem_token_valido_e_recusada(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    runner = SimpleRunner(settings, TokenStore(settings))

    resultado = runner.executar(
        ExecutionRequest(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=HASH_DIFUSAO,
            approval_token="token-desconhecido",
            command=(sys.executable, "-c", "print('ok')"),
        )
    )

    assert resultado.tool_result.status is ToolStatus.FAILED
    assert "aprovação" in (resultado.error or "")
    assert resultado.isolated is False
    assert not list(settings.data_dir.glob("exec-*"))


def test_timeout_termina_processo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    inicio = time.monotonic()

    resultado = runner.executar(
        ExecutionRequest(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=HASH_DIFUSAO,
            approval_token=_token(store),
            command=(sys.executable, "-c", "import time; time.sleep(10)"),
            timeout_s=0.5,
        )
    )

    assert resultado.tool_result.status is ToolStatus.FAILED
    assert "Tempo limite" in (resultado.error or "")
    assert time.monotonic() - inicio < LIMITE_SEGUNDOS


def test_cancelamento_termina_processo(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    sinal = threading.Event()

    def cancelar() -> None:
        time.sleep(0.3)
        sinal.set()

    tarefa = threading.Thread(target=cancelar)
    tarefa.start()
    inicio = time.monotonic()
    resultado = runner.executar(
        ExecutionRequest(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=HASH_DIFUSAO,
            approval_token=_token(store),
            command=(sys.executable, "-c", "import time; time.sleep(10)"),
            timeout_s=10,
            cancel_event=sinal,
        )
    )
    tarefa.join()

    assert resultado.tool_result.status is ToolStatus.FAILED
    assert "cancelada" in (resultado.error or "").lower()
    assert time.monotonic() - inicio < LIMITE_SEGUNDOS
