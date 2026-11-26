"""Testes de segurança dos tokens de aprovação da interface local."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from agents.runner import parse_agent_output
from approvals.tokens import (
    ApprovalDenied,
    DiffAlterado,
    SolicitacaoAprovacao,
    TokenStore,
)

from app.core.config import load_settings

if TYPE_CHECKING:
    from pathlib import Path

    from app.core.config import Settings

HASH_UM = "a" * 64
HASH_DOIS = "b" * 64
AGORA = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765


def _settings(tmp_path: Path, *, ui_enabled: bool = True) -> Settings:
    """Carrega configuração de teste sem credenciais reais."""
    base = tmp_path / "project"
    base.mkdir()
    valores = {"HCW_UI_TOKEN": TOKEN_FALSO}
    if ui_enabled:
        valores["HCW_UI_ENABLED"] = "true"
    return load_settings(valores, base_dir=base)


def _solicitacao(
    *,
    headers: dict[str, str] | None = None,
    diff_hash: str = HASH_UM,
) -> SolicitacaoAprovacao:
    """Constrói pedido com cabeçalhos configuráveis para testes de ataque."""
    cabecalhos = headers or {
        "Authorization": f"Bearer {TOKEN_FALSO}",
        "Origin": f"http://127.0.0.1:{PORTA}",
    }
    return SolicitacaoAprovacao(
        task_id="tarefa-1",
        correlation_id="correlacao-1",
        diff_hash=diff_hash,
        headers=cabecalhos,
        porta=PORTA,
    )


def test_pedido_sem_bearer_nao_emite_token(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=lambda: AGORA)

    with pytest.raises(ApprovalDenied, match="servidor da UI"):
        store.emitir(_solicitacao(headers={"Origin": f"http://127.0.0.1:{PORTA}"}))

    assert store.quantidade == 0


def test_origem_falsa_nao_emite_token(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=lambda: AGORA)
    cabecalhos = {
        "Authorization": f"Bearer {TOKEN_FALSO}",
        "Origin": "http://atacante.example",
    }

    with pytest.raises(ApprovalDenied, match="servidor da UI"):
        store.emitir(_solicitacao(headers=cabecalhos))

    assert store.quantidade == 0


def test_interface_desligada_nao_emite_token(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path, ui_enabled=False), relogio=lambda: AGORA)

    with pytest.raises(ApprovalDenied, match="servidor da UI"):
        store.emitir(_solicitacao())

    assert store.quantidade == 0


def test_saida_do_modelo_com_approved_true_nao_emite_token(
    tmp_path: Path,
) -> None:
    store = TokenStore(_settings(tmp_path), relogio=lambda: AGORA)
    resposta = json.dumps(
        {
            "summary": "Plano pronto.",
            "evidence": ["tests passaram"],
            "approved": True,
        }
    )
    saida = parse_agent_output(resposta)

    assert saida.approval_claim is True
    with pytest.raises(ApprovalDenied, match="servidor da UI"):
        store.emitir(_solicitacao(headers={"Content-Type": "application/json"}))
    assert store.quantidade == 0


def test_reutilizacao_com_diff_alterado_e_recusada_sem_logs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = TokenStore(_settings(tmp_path), relogio=lambda: AGORA)
    token = store.emitir(_solicitacao())

    with pytest.raises(DiffAlterado, match="diff mudou"):
        store.validar(token.token, "tarefa-1", HASH_DOIS)

    capturado = capsys.readouterr()
    assert token.token not in capturado.out
    assert token.token not in capturado.err
