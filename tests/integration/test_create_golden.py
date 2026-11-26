"""Caso dourado da calculadora com fluxo CREATE e pytest real."""

from __future__ import annotations

import hashlib
import json
import socket
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from agents.definitions import AgentDefinition, parse_agent_definition
from agents.runner import AgentRunner, RunnerConfig
from approvals.tokens import SolicitacaoAprovacao, TokenStore
from execution import ExecutionRequest, SimpleRunner
from workflows.create import (
    PASSOS,
    CheckpointStore,
    CreateRequest,
    CreateWorkflow,
    Step,
    WorkflowDependencies,
    hash_token,
)

from app.core.config import Settings, load_settings
from app.core.events import Event, EventBus
from app.core.results import ToolStatus
from app.core.tasks import SqliteTaskStore, TaskStatus
from app.llm.contracts import ModelRequest, ModelResponse, ProviderKind

TAREFA = "hcw-04-008-golden"
CORRELACAO = "corr-hcw-04-008-golden"
DIFF_HASH = "cc1631c25d9fe07728b20012b719d4692ef775b99b3a6464f15d3a5d922c4e21"
TOKEN_DOURADO = "token-dourado-hcw-04-008"
TOKEN_UI = "token-ui-dourado-16"
PORTA = 8765
LIMITE_S = 30
RELATORIO = Path(__file__).resolve().parents[2] / "docs/reports/phase-04-golden.md"
FIXTURA = Path(__file__).resolve().parent.parent / "eval/fixtures/calculadora_cli"
PASSOS_AGENTE = tuple(
    passo for passo in PASSOS if passo not in (Step.PEDIDO, Step.APROVACAO)
)

DEFINICAO = """---
id: planeador
nome: Planeador
versao: 1
entrada: texto
saida: json
ferramentas: leitura
---
Devolve resumo e evidência verificável em JSON.
"""


class DestinoEventos:
    """Destino em memória para verificar a rastreabilidade dos eventos."""

    def __init__(self) -> None:
        self.eventos: list[Event] = []

    def write(self, evento: Event) -> None:
        """Guarda o evento recebido."""
        self.eventos.append(evento)


class FornecedorFalso:
    """Fornecedor local determinístico sem acesso à rede."""

    provider = ProviderKind.FAKE

    def __init__(self, respostas: Sequence[str]) -> None:
        self._respostas = list(respostas)
        self.pedidos: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Devolve a próxima resposta pré-definida."""
        self.pedidos.append(request)
        return ModelResponse(
            provider=self.provider,
            model=request.model,
            text=self._respostas.pop(0),
            task_id=request.task_id,
            correlation_id=request.correlation_id,
            latency_ms=0,
        )


def _resposta(passo: Step) -> str:
    return json.dumps(
        {"summary": f"dourado {passo.value}", "evidence": [f"create/{passo.value}"]}
    )


def _definicoes() -> dict[str, AgentDefinition]:
    identificadores = ("planeador", "arquitecto", "implementador", "revisor", "relator")
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
        {"HCW_CREATE_FLOW": "true", "HCW_UI_ENABLED": "true", "HCW_UI_TOKEN": TOKEN_UI},
        base_dir=base,
    )


def _dependencias(
    tmp_path: Path,
    settings: Settings,
    fornecedor: FornecedorFalso,
    destino: DestinoEventos,
    tokens: TokenStore | None = None,
) -> tuple[WorkflowDependencies, TokenStore]:
    runner = AgentRunner(
        provider=fornecedor,
        config=RunnerConfig(
            provider_kind=ProviderKind.FAKE,
            model="fake-model",
            timeout_s=LIMITE_S,
            max_retries=0,
        ),
        definitions=_definicoes(),
        event_sink=destino,
    )
    emissor = tokens or TokenStore(settings)
    tarefas = SqliteTaskStore(tmp_path / "tasks.sqlite3")
    tarefas.initialize()
    deps = WorkflowDependencies(
        settings=settings,
        tasks=tarefas,
        checkpoints=CheckpointStore(tmp_path / "checkpoints.sqlite3"),
        events=EventBus([destino]),
        runner=runner,
        tokens=emissor,
    )
    return deps, emissor


def _token(tokens: TokenStore) -> str:
    return tokens.emitir(
        SolicitacaoAprovacao(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=DIFF_HASH,
            porta=PORTA,
            headers={
                "Origin": f"http://127.0.0.1:{PORTA}",
                "Authorization": f"Bearer {TOKEN_UI}",
                "Sec-Fetch-Site": "same-origin",
            },
        )
    ).token


def _pedido(token: str | None = None) -> CreateRequest:
    return CreateRequest(
        task_id=TAREFA,
        correlation_id=CORRELACAO,
        pedido="Criar calculadora de linha de comandos com testes.",
        diff_hash=DIFF_HASH,
        token_aprovacao=token,
        chaves={passo.value: f"golden-{passo.value}" for passo in PASSOS},
    )


def _arquivos() -> dict[str, str]:
    return {
        nome: (FIXTURA / nome).read_text(encoding="utf-8")
        for nome in ("main.py", "test_main.py")
    }


def _bootstrap(arquivos: Mapping[str, str]) -> str:
    pares = ", ".join(f"{nome!r}: {conteudo!r}" for nome, conteudo in arquivos.items())
    return (
        "import os\n"
        "import pathlib\n"
        "import sys\n"
        "raiz = pathlib.Path.cwd()\n"
        "os.environ['TEMP'] = str(raiz)\n"
        "os.environ['TMP'] = str(raiz)\n"
        "os.environ['TMPDIR'] = str(raiz)\n"
        "import pytest\n"
        f"arquivos = {{{pares}}}\n"
        "for nome, conteudo in arquivos.items():\n"
        "    pathlib.Path(nome).write_text(conteudo, encoding='utf-8')\n"
        "sys.exit(pytest.main(['-q', 'test_main.py']))\n"
    )


def _bloquear_rede(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    tentativas: list[object] = []

    def negar(*args: object, **kwargs: object) -> None:
        tentativas.append((args, kwargs))
        raise AssertionError("Pedido externo observado durante o caso dourado.")

    monkeypatch.setattr(socket, "getaddrinfo", negar)
    monkeypatch.setattr(socket, "create_connection", negar)
    monkeypatch.setattr(socket.socket, "connect", negar)
    monkeypatch.setattr(socket.socket, "connect_ex", negar)
    return tentativas


def test_caso_dourado_calculadora_ponta_a_ponta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arquivos = _arquivos()
    assert (
        hashlib.sha256(
            "".join(
                f"{nome}\0{conteudo}\0" for nome, conteudo in sorted(arquivos.items())
            ).encode("utf-8")
        ).hexdigest()
        == DIFF_HASH
    )
    monkeypatch.setattr(
        "approvals.tokens.store.secrets.token_urlsafe", lambda _tamanho: TOKEN_DOURADO
    )
    tentativas_rede = _bloquear_rede(monkeypatch)

    settings = _settings(tmp_path)
    destino = DestinoEventos()
    fornecedor = FornecedorFalso([_resposta(passo) for passo in PASSOS_AGENTE])
    deps, tokens = _dependencias(tmp_path, settings, fornecedor, destino)
    fluxo = CreateWorkflow(deps)
    parado = fluxo.executar(_pedido())

    assert parado.aguardando_aprovacao is True
    assert parado.checkpoint.last_completed_step is Step.ARQUITECTURA

    aprovado = fluxo.executar(_pedido(_token(tokens)))
    assert aprovado.status is TaskStatus.COMPLETED
    assert aprovado.last_completed_step is Step.RELATORIO
    assert aprovado.checkpoint.pending_token_hash == hash_token(TOKEN_DOURADO)
    assert len(fornecedor.pedidos) == len(PASSOS_AGENTE)
    assert all(pedido.task_id == TAREFA for pedido in fornecedor.pedidos)

    executor = SimpleRunner(settings, tokens, EventBus([destino]))
    resultado = executor.executar(
        ExecutionRequest(
            task_id=TAREFA,
            correlation_id=CORRELACAO,
            diff_hash=DIFF_HASH,
            approval_token=TOKEN_DOURADO,
            command=(sys.executable, "-c", _bootstrap(arquivos)),
            timeout_s=LIMITE_S,
        )
    )

    assert resultado.tool_result.status is ToolStatus.DONE
    assert resultado.isolated is False
    assert resultado.returncode == 0
    assert "4 passed" in resultado.stdout
    assert "failed" not in resultado.stdout
    evidencia = "\n".join(resultado.tool_result.evidence)
    assert "returncode=0" in evidencia
    assert "stdout_sha256=" in evidencia

    concluido = next(
        evento for evento in destino.eventos if evento.kind == "execution.concluido"
    )
    assert concluido.task_id == TAREFA
    assert concluido.correlation_id == CORRELACAO
    assert concluido.data["returncode"] == 0
    assert tentativas_rede == []

    relatorio = RELATORIO.read_text(encoding="utf-8")
    assert "ToolResult.DONE" in relatorio
    assert DIFF_HASH in relatorio
    assert hash_token(TOKEN_DOURADO) in relatorio
    assert CORRELACAO in relatorio
    assert TOKEN_DOURADO not in relatorio
