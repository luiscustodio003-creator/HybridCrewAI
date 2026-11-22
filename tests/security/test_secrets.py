"""Testes da abstracção de segredos sem gravação em ficheiros."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import (
    EnvironmentSecrets,
    SecretError,
    Secrets,
    SecretStr,
    load_settings,
    redact,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

FAKE_KEY = "sk-TEST-NAO-GRAVAR"


class FakeProvider:
    """Fornecedor em memória, sem acesso a disco."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = values

    def get(self, name: str) -> str | None:
        """Devolve o valor de um nome permitido."""
        return self._values.get(name)


def test_segredo_nao_aparece_em_str_nem_repr() -> None:
    secret = SecretStr(FAKE_KEY)
    assert secret.reveal() == FAKE_KEY
    assert FAKE_KEY not in str(secret)
    assert FAKE_KEY not in repr(secret)


def test_segredo_lido_apenas_do_fornecedor_injetado() -> None:
    store = Secrets(FakeProvider({"GEMINI_API_KEY": FAKE_KEY}), ("GEMINI_API_KEY",))
    secret = store.require("GEMINI_API_KEY")
    assert secret.reveal() == FAKE_KEY
    assert FAKE_KEY not in repr(store)


def test_nome_nao_declarado_e_recusado() -> None:
    store = Secrets(EnvironmentSecrets({"GEMINI_API_KEY": FAKE_KEY}))
    with pytest.raises(SecretError, match="OUTRO"):
        store.get("OUTRO")


def test_nome_invalido_e_recusado() -> None:
    store = Secrets(FakeProvider({"gemini-api-key": FAKE_KEY}), ("gemini-api-key",))
    with pytest.raises(SecretError, match="inválido"):
        store.get("gemini-api-key")


def test_require_sem_valor_aborta_com_nome() -> None:
    store = Secrets(EnvironmentSecrets({}))
    with pytest.raises(SecretError, match="GEMINI_API_KEY"):
        store.require("GEMINI_API_KEY")


def test_valor_vazio_conta_como_ausente() -> None:
    store = Secrets(EnvironmentSecrets({"GEMINI_API_KEY": "   "}))
    assert store.get("GEMINI_API_KEY") is None


def test_valor_falso_da_configuracao_nao_e_persistido(tmp_path: Path) -> None:
    env = {"HCW_API_KEY": FAKE_KEY}
    settings = load_settings(env, base_dir=tmp_path)
    store = Secrets(EnvironmentSecrets(env), ("HCW_API_KEY",))
    secret = store.require("HCW_API_KEY")
    assert not hasattr(settings, "api_key")
    assert FAKE_KEY not in repr(settings)
    assert FAKE_KEY not in repr(secret)
    assert list(tmp_path.iterdir()) == []


def test_redaccao_remove_valor_de_texto() -> None:
    secret = SecretStr(FAKE_KEY)
    assert redact(f"chave={FAKE_KEY}", [secret]) == "chave=***REDACTED***"


def test_redaccao_ignora_segredos_vazios() -> None:
    assert redact("sem segredo", [SecretStr("")]) == "sem segredo"
