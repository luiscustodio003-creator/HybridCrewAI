"""Testes de segurança do executor simples não isolado."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from approvals.tokens import SolicitacaoAprovacao, TokenStore
from execution import ExecutionRequest, SimpleRunner

from app.core.config import load_settings
from app.core.results import ToolStatus

if TYPE_CHECKING:
    from app.core.config import Settings

HASH_DIFUSAO = "a" * 64
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765


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
    task_id: str,
    correlation_id: str,
) -> str:
    """Emite token autenticado para a tarefa indicada."""
    return store.emitir(
        SolicitacaoAprovacao(
            task_id=task_id,
            correlation_id=correlation_id,
            diff_hash=HASH_DIFUSAO,
            headers={
                "Authorization": f"Bearer {TOKEN_FALSO}",
                "Origin": f"http://127.0.0.1:{PORTA}",
            },
            porta=PORTA,
        )
    ).token


def test_subprocesso_sem_rede_e_sem_segredes(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    codigo = (
        "import os, urllib.request\n"
        "print('SEGREDOS=' + ','.join(k for k in os.environ if 'TOKEN' in k.upper()))\n"
        "print('AMBIENTE=' + ','.join(sorted(os.environ)))\n"
        "urllib.request.urlopen('http://127.0.0.1:9', timeout=1)\n"
    )

    token = _token(store, task_id="tarefa-rede", correlation_id="correlacao-rede")
    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-rede",
            correlation_id="correlacao-rede",
            diff_hash=HASH_DIFUSAO,
            approval_token=token,
            command=(sys.executable, "-c", codigo),
            timeout_s=10,
        )
    )

    combinado = (resultado.stdout or "") + (resultado.stderr or "")
    ambiente = (resultado.stdout or "").split("AMBIENTE=", 1)[1].splitlines()[0]
    chaves_hcw = [chave for chave in ambiente.split(",") if chave.startswith("HCW_")]
    assert resultado.returncode != 0
    assert "Rede desactivada" in combinado
    assert "HCW_UI_TOKEN" not in combinado
    assert "SEGREDOS=" in (resultado.stdout or "")
    assert chaves_hcw == ["HCW_EXEC_WORKSPACE"]


def test_pytest_da_venv_pode_ser_lido(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    token = _token(store, task_id="tarefa-pytest", correlation_id="correlacao-pytest")

    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-pytest",
            correlation_id="correlacao-pytest",
            diff_hash=HASH_DIFUSAO,
            approval_token=token,
            command=(sys.executable, "-c", "import pytest; print(pytest.__version__)"),
            timeout_s=10,
        )
    )

    assert resultado.tool_result.status is ToolStatus.DONE
    assert resultado.returncode == 0
    assert resultado.stdout.strip()


def test_subprocesso_nao_le_ficheiro_fora_da_pasta(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    segredo = tmp_path / "segredo.txt"
    segredo.write_text("conteudo-proibido", encoding="utf-8")
    token = _token(store, task_id="tarefa-leitura", correlation_id="correlacao-leitura")

    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-leitura",
            correlation_id="correlacao-leitura",
            diff_hash=HASH_DIFUSAO,
            approval_token=token,
            command=(sys.executable, "-c", f"print(open({str(segredo)!r}).read())"),
            timeout_s=10,
        )
    )

    assert resultado.returncode != 0
    assert "fora da pasta autorizada" in (resultado.stderr or "")


def test_subprocesso_nao_escreve_fora_da_pasta(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    destino = tmp_path / "escrita-fora.txt"
    token = _token(store, task_id="tarefa-escrita", correlation_id="correlacao-escrita")

    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-escrita",
            correlation_id="correlacao-escrita",
            diff_hash=HASH_DIFUSAO,
            approval_token=token,
            command=(sys.executable, "-c", f"open({str(destino)!r}, 'w').write('x')"),
            timeout_s=10,
        )
    )

    assert resultado.returncode != 0
    assert "fora da pasta autorizada" in (resultado.stderr or "")
    assert not destino.exists()


def test_token_de_outra_tarefa_nao_executa(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)
    token = _token(store, task_id="tarefa-aprovada", correlation_id="corr-aprovada")

    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-atacante",
            correlation_id="corr-aprovada",
            diff_hash=HASH_DIFUSAO,
            approval_token=token,
            command=(sys.executable, "-c", "print('executou')"),
        )
    )

    assert resultado.tool_result.status is ToolStatus.FAILED
    assert "tarefa" in (resultado.error or "")
    assert not list(settings.data_dir.glob("exec-*"))


def test_correlacao_divergente_nao_executa(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    store = TokenStore(settings)
    runner = SimpleRunner(settings, store)

    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-correlacao",
            correlation_id="corr-atacante",
            diff_hash=HASH_DIFUSAO,
            approval_token=_token(
                store, task_id="tarefa-correlacao", correlation_id="corr-autorizada"
            ),
            command=(sys.executable, "-c", "print('executou')"),
        )
    )

    assert resultado.tool_result.status is ToolStatus.FAILED
    assert "correlação" in (resultado.error or "")
