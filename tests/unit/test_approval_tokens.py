"""Testes unitários dos tokens de aprovação emitidos pela interface."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from approvals.tokens import (
    VALIDADE_MINUTOS,
    DadosInvalidos,
    DiffAlterado,
    SolicitacaoAprovacao,
    TarefaInvalida,
    TokenExpirado,
    TokenInvalido,
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


class RelogioFalso:
    """Relógio injectado para controlar a expiração sem esperar."""

    def __init__(self, agora: datetime) -> None:
        self.agora = agora

    def __call__(self) -> datetime:
        return self.agora


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração com interface activa e token de teste óbvio."""
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {
            "HCW_UI_ENABLED": "true",
            "HCW_UI_TOKEN": TOKEN_FALSO,
        },
        base_dir=base,
    )


def _solicitacao(
    *,
    task_id: str = "tarefa-1",
    correlation_id: str = "correlacao-1",
    diff_hash: str = HASH_UM,
    headers: dict[str, str] | None = None,
) -> SolicitacaoAprovacao:
    """Constrói um pedido autenticado como o servidor da UI faria."""
    cabecalhos = headers or {
        "Authorization": f"Bearer {TOKEN_FALSO}",
        "Origin": f"http://127.0.0.1:{PORTA}",
    }
    return SolicitacaoAprovacao(
        task_id=task_id,
        correlation_id=correlation_id,
        diff_hash=diff_hash,
        headers=cabecalhos,
        porta=PORTA,
    )


def test_token_e_ligado_a_tarefa_hash_e_expiracao(tmp_path: Path) -> None:
    relogio = RelogioFalso(AGORA)
    store = TokenStore(_settings(tmp_path), relogio=relogio)

    token = store.emitir(_solicitacao())

    assert token.task_id == "tarefa-1"
    assert token.correlation_id == "correlacao-1"
    assert token.diff_hash == HASH_UM
    assert token.emitido_em == AGORA
    assert token.expira_em - token.emitido_em == timedelta(minutes=VALIDADE_MINUTOS)
    assert token.token not in repr(token)


def test_token_valido_e_aceite_com_mesmo_diff(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))
    token = store.emitir(_solicitacao())

    validado = store.validar(token.token, "tarefa-1", HASH_UM)

    assert validado == token


def test_diff_alterado_e_recusado(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))
    token = store.emitir(_solicitacao())

    with pytest.raises(DiffAlterado, match="diff mudou"):
        store.validar(token.token, "tarefa-1", HASH_DOIS)


def test_token_expirado_e_recusado(tmp_path: Path) -> None:
    relogio = RelogioFalso(AGORA)
    store = TokenStore(_settings(tmp_path), relogio=relogio)
    token = store.emitir(_solicitacao())

    relogio.agora = AGORA + timedelta(minutes=VALIDADE_MINUTOS)

    with pytest.raises(TokenExpirado, match="expirou"):
        store.validar(token.token, "tarefa-1", HASH_UM)


def test_tarefa_diferente_e_recusada(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))
    token = store.emitir(_solicitacao())

    with pytest.raises(TarefaInvalida, match="tarefa"):
        store.validar(token.token, "outra-tarefa", HASH_UM)


def test_token_desconhecido_e_recusado(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))

    with pytest.raises(TokenInvalido, match="desconhecido"):
        store.validar("token-que-nao-existe", "tarefa-1", HASH_UM)


def test_hash_do_diff_invalido_e_recusado_antes_de_emitir(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))

    with pytest.raises(DadosInvalidos, match="SHA-256"):
        store.emitir(_solicitacao(diff_hash="abc"))

    assert store.quantidade == 0


def test_identificadores_vazios_sao_recusados(tmp_path: Path) -> None:
    store = TokenStore(_settings(tmp_path), relogio=RelogioFalso(AGORA))

    with pytest.raises(DadosInvalidos, match="task_id"):
        store.emitir(_solicitacao(task_id="  "))

    with pytest.raises(DadosInvalidos, match="correlation_id"):
        store.emitir(_solicitacao(correlation_id=""))

    assert store.quantidade == 0
