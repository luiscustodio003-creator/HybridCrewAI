"""Integração do diff real do workspace com a aprovação da interface local."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import load_settings
from app.ui.server import APPROVALS_PATH, DIFF_PATH, UiServer, create_server
from app.workspace import (
    SnapshotLimits,
    create_snapshot,
    inventory_workspace,
    load_snapshot,
    snapshot_digest,
)

if TYPE_CHECKING:
    from app.core.config import Settings

TOKEN_FALSO = "token-falso-com-16"
TAREFA = "tarefa-workspace-009"
CORRELACAO = "correlacao-workspace-009"
OK = 200
ERRO = 400
NAO_AUTORIZADO = 401
NAO_ENCONTRADO = 404


def _settings(tmp_path: Path, *, diff: bool = True) -> Settings:
    """Carrega configuração isolada com o interruptor de diff escolhido."""
    base = tmp_path / "project"
    base.mkdir(parents=True, exist_ok=True)
    ambiente: Mapping[str, str] = {
        "HCW_UI_ENABLED": "true",
        "HCW_UI_TOKEN": TOKEN_FALSO,
        "HCW_DIFF": "true" if diff else "false",
    }
    return load_settings(ambiente, base_dir=base)


def _limites(settings: Settings) -> SnapshotLimits:
    """Devolve limites de snapshot derivados da configuração isolada."""
    return SnapshotLimits(
        max_chars=settings.max_workspace_path_chars,
        max_file_bytes=settings.max_workspace_file_bytes,
        max_total_bytes=settings.max_workspace_file_bytes * 10,
        max_files=100,
    )


@contextmanager
def _servidor(settings: Settings) -> Iterator[UiServer]:
    """Inicia e fecha um servidor real num porto efémero."""
    servidor = create_server(settings)
    tarefa = threading.Thread(target=servidor.serve_forever, daemon=True)
    tarefa.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()
        tarefa.join(timeout=2)


def _porta(servidor: UiServer) -> int:
    """Lê o porto do servidor sem depender da classe concreta."""
    return int(servidor.server_port)


def _cabecalhos(servidor: UiServer) -> Mapping[str, str]:
    """Devolve cabeçalhos válidos para o porto do servidor."""
    return {
        "Origin": f"http://127.0.0.1:{_porta(servidor)}",
        "Authorization": f"Bearer {TOKEN_FALSO}",
    }


def _pedido(
    servidor: UiServer,
    metodo: str,
    caminho: str,
    cabecalhos: Mapping[str, str],
    corpo: bytes | None = None,
) -> tuple[int, str]:
    """Faz um pedido HTTP real ao servidor local."""
    ligacao = HTTPConnection("127.0.0.1", _porta(servidor), timeout=2)
    try:
        ligacao.request(metodo, caminho, body=corpo, headers=dict(cabecalhos))
        resposta = ligacao.getresponse()
        return resposta.status, resposta.read().decode("utf-8")
    finally:
        ligacao.close()


def _preparar_workspace(settings: Settings) -> tuple[Path, str]:
    """Cria um ficheiro, guarda o snapshot e altera o ficheiro."""
    raiz = settings.workspace_dir
    raiz.mkdir(parents=True, exist_ok=True)
    alvo = raiz / "main.py"
    alvo.write_text("print('original')\n", encoding="utf-8")
    instantaneo = create_snapshot(raiz, limits=_limites(settings))
    alvo.write_text("print('alterado')\n", encoding="utf-8")
    return raiz, instantaneo.id


def _caminho_diff(snapshot_id: str) -> str:
    """Monta a consulta do diff com os identificadores da tarefa."""
    return (
        f"{DIFF_PATH}?task_id={TAREFA}"
        f"&correlation_id={CORRELACAO}&snapshot_id={snapshot_id}"
    )


def _diff_esperado(raiz: Path, settings: Settings, snapshot_id: str) -> tuple[str, str]:
    """Calcula o diff esperado a partir dos hashes reais verificáveis."""
    instantaneo = load_snapshot(raiz, snapshot_id, limits=_limites(settings))
    alteracao = snapshot_digest(inventory_workspace(raiz, limits=_limites(settings)))
    serializado = json.dumps(
        {"snapshot_hash": instantaneo.digest, "alteracao_hash": alteracao},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest(), alteracao


def _obter_diff(
    servidor: UiServer, snapshot_id: str
) -> tuple[int, str, dict[str, object]]:
    """Obtém o diff pela rota autenticada da interface."""
    estado, texto = _pedido(
        servidor, "GET", _caminho_diff(snapshot_id), _cabecalhos(servidor)
    )
    return estado, texto, json.loads(texto) if estado == OK else {}


def test_diff_real_e_aprovacao_ligada_ao_token(tmp_path: Path) -> None:
    """O token só é emitido para o diff real e para a tarefa apresentada."""
    settings = _settings(tmp_path)
    raiz, snapshot_id = _preparar_workspace(settings)
    esperado, alteracao = _diff_esperado(raiz, settings, snapshot_id)

    with _servidor(settings) as servidor:
        estado, _, dados = _obter_diff(servidor, snapshot_id)
        assert estado == OK
        assert dados["diff_hash"] == esperado
        assert dados["alteracao_hash"] == alteracao
        assert dados["task_id"] == TAREFA
        assert dados["correlation_id"] == CORRELACAO

        corpo = json.dumps(
            {
                "task_id": TAREFA,
                "correlation_id": CORRELACAO,
                "diff_hash": dados["diff_hash"],
            }
        ).encode("utf-8")
        estado, texto = _pedido(
            servidor, "POST", APPROVALS_PATH, _cabecalhos(servidor), corpo
        )
        assert estado == OK
        aprovacao = json.loads(texto)
        token = str(aprovacao["token"])
        validada = servidor.tokens.validar(token, TAREFA, str(dados["diff_hash"]))
        assert validada.correlation_id == CORRELACAO

        _, html = _pedido(servidor, "GET", "/", _cabecalhos(servidor))
        _, javascript = _pedido(
            servidor, "GET", "/approvals.js", _cabecalhos(servidor)
        )
        assert token not in html
        assert token not in javascript
        assert token not in _caminho_diff(snapshot_id)
        assert token not in APPROVALS_PATH
        assert "localStorage" not in javascript
        assert "sessionStorage" not in javascript


def test_aprovado_true_do_modelo_nao_emite_token(tmp_path: Path) -> None:
    """Um campo extra do modelo não pode gerar aprovação."""
    settings = _settings(tmp_path)
    _, snapshot_id = _preparar_workspace(settings)

    with _servidor(settings) as servidor:
        estado, _, dados = _obter_diff(servidor, snapshot_id)
        assert estado == OK
        corpo = json.dumps(
            {
                "task_id": TAREFA,
                "correlation_id": CORRELACAO,
                "diff_hash": dados["diff_hash"],
                "approved": True,
            }
        ).encode("utf-8")
        estado, texto = _pedido(
            servidor, "POST", APPROVALS_PATH, _cabecalhos(servidor), corpo
        )
        assert estado == ERRO
        assert "token" not in texto


def test_snapshot_adulterado_nao_devolve_diff(tmp_path: Path) -> None:
    """Um snapshot alterado não pode servir de base ao hash do diff."""
    settings = _settings(tmp_path)
    raiz, snapshot_id = _preparar_workspace(settings)
    alvo = raiz / ".snapshots" / snapshot_id / "main.py"
    alvo.write_text("print('adulterado')\n", encoding="utf-8")

    with _servidor(settings) as servidor:
        estado, texto = _pedido(
            servidor, "GET", _caminho_diff(snapshot_id), _cabecalhos(servidor)
        )
        assert estado == ERRO
        assert "diff_hash" not in texto


def test_diff_sem_token_e_recusado(tmp_path: Path) -> None:
    """A rota do diff exige o token local como qualquer API."""
    settings = _settings(tmp_path)
    _, snapshot_id = _preparar_workspace(settings)
    cabecalhos = {"Origin": f"http://127.0.0.1:{0}"}

    with _servidor(settings) as servidor:
        cabecalhos = {"Origin": f"http://127.0.0.1:{_porta(servidor)}"}
        estado, texto = _pedido(
            servidor, "GET", _caminho_diff(snapshot_id), cabecalhos
        )
        assert estado == NAO_AUTORIZADO
        assert "diff_hash" not in texto


def test_diff_sem_interruptor_nao_existe(tmp_path: Path) -> None:
    """O diff não é exposto quando o interruptor está desligado."""
    settings = _settings(tmp_path, diff=False)
    _, snapshot_id = _preparar_workspace(settings)

    with _servidor(settings) as servidor:
        estado, texto = _pedido(
            servidor, "GET", _caminho_diff(snapshot_id), _cabecalhos(servidor)
        )
        assert estado == NAO_ENCONTRADO
        assert "diff_hash" not in texto


@pytest.mark.parametrize("campo", ["task_id", "correlation_id", "snapshot_id"])
def test_diff_sem_identificador_e_recusado(tmp_path: Path, campo: str) -> None:
    """A rota do diff exige os identificadores que ligam o token à tarefa."""
    settings = _settings(tmp_path)
    _, snapshot_id = _preparar_workspace(settings)
    consulta = {
        "task_id": TAREFA,
        "correlation_id": CORRELACAO,
        "snapshot_id": snapshot_id,
    }
    consulta.pop(campo)
    caminho = DIFF_PATH + "?" + "&".join(
        f"{nome}={valor}" for nome, valor in consulta.items()
    )

    with _servidor(settings) as servidor:
        estado, texto = _pedido(servidor, "GET", caminho, _cabecalhos(servidor))
        assert estado == ERRO
        assert "diff_hash" not in texto
