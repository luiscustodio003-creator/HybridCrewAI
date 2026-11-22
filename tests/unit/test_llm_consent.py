"""Testes de consentimento cloud e tipo de conta Gemini."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.core.config.defaults import GEMINI_ACCOUNT_TYPE_DEFAULT
from app.llm.consent import AccountType, CloudConsentStore, ConsentError
from app.llm.egress import CloudDenied, EgressPolicy

URL_CLOUD = "https://api.example.com/v1/model"


def test_primeiro_pedido_cloud_sem_consentimento_e_acionavel_e_sem_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chamadas: list[Any] = []

    def urlopen_bloqueado(*args: object, **kwargs: object) -> None:
        chamadas.append((args, kwargs))
        raise AssertionError("Não devia abrir socket")

    monkeypatch.setattr("urllib.request.urlopen", urlopen_bloqueado)
    consentimento = CloudConsentStore(tmp_path / "consent.sqlite3")
    consentimento.initialize()
    politica = EgressPolicy(allow_cloud=True, allow_local=False)

    with pytest.raises(CloudDenied, match="autorize explicitamente"):
        politica.send_json(URL_CLOUD, {}, {"prompt": "olá"}, consent=consentimento)

    assert chamadas == []


def test_consentimento_e_tipo_de_conta_persistem_sem_credenciais(tmp_path: Path) -> None:
    caminho = tmp_path / "consent.sqlite3"
    consentimento = CloudConsentStore(caminho)
    consentimento.initialize()
    consentimento.grant(AccountType.WORK)

    registo = CloudConsentStore(caminho).get()
    assert registo.account_type is AccountType.WORK
    assert registo.granted is True

    with sqlite3.connect(caminho) as ligacao:
        colunas = {
            linha[1]
            for linha in ligacao.execute("PRAGMA table_info(cloud_consent)")
        }
        linhas = ligacao.execute(
            "SELECT account_type, granted FROM cloud_consent"
        ).fetchall()
    assert colunas == {"singleton", "account_type", "granted", "updated_at"}
    assert linhas == [("work", 1)]
    assert not any(
        nome in colunas for nome in ("credential", "token", "key", "secret", "password")
    )

    conteudo = caminho.read_bytes()
    assert b"sk-" not in conteudo
    assert b"api_key" not in conteudo


def test_tipo_desconhecido_nunca_autoriza_cloud(tmp_path: Path) -> None:
    consentimento = CloudConsentStore(tmp_path / "consent.sqlite3")
    consentimento.initialize()
    registo = consentimento.grant(AccountType.UNKNOWN)

    assert registo.account_type is AccountType.UNKNOWN
    assert registo.granted is False
    assert consentimento.allows_cloud() is False
    assert CloudConsentStore(tmp_path / "consent.sqlite3").get().account_type is AccountType.UNKNOWN


def test_revogacao_bloqueia_pedidos_cloud_seguintes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chamadas: list[Any] = []

    def urlopen_bloqueado(*args: object, **kwargs: object) -> None:
        chamadas.append((args, kwargs))
        raise AssertionError("Não devia abrir socket")

    monkeypatch.setattr("urllib.request.urlopen", urlopen_bloqueado)
    consentimento = CloudConsentStore(tmp_path / "consent.sqlite3")
    consentimento.initialize()
    consentimento.grant(AccountType.PERSONAL)
    politica = EgressPolicy(allow_cloud=True, allow_local=False)

    assert consentimento.allows_cloud() is True
    consentimento.revoke()
    with pytest.raises(CloudDenied):
        politica.send_json(URL_CLOUD, {}, {"prompt": "olá"}, consent=consentimento)
    assert chamadas == []


def test_tipo_de_conta_invalido_e_recusado(tmp_path: Path) -> None:
    consentimento = CloudConsentStore(tmp_path / "consent.sqlite3")
    consentimento.initialize()
    with pytest.raises(ConsentError):
        consentimento.grant("escolar")
    assert consentimento.get().account_type.value == GEMINI_ACCOUNT_TYPE_DEFAULT
