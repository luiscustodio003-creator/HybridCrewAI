"""Testes da configuração da interface web local."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import ConfigError, load_settings
from app.ui import require_ui_token, ui_enabled

if TYPE_CHECKING:
    from collections.abc import Mapping

TOKEN_FALSO = "token-falso-com-16"


def _base_dir(tmp_path: Path) -> Path:
    """Devolve um directório base isolado para cada teste."""
    base = tmp_path / "project"
    base.mkdir()
    return base


def test_interface_desligada_por_omissao(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    assert settings.ui_enabled is False
    assert settings.ui_token is None
    assert ui_enabled(settings) is False


def test_token_falso_e_lido_quando_interface_ativada(tmp_path: Path) -> None:
    env: Mapping[str, str] = {
        "HCW_UI_ENABLED": "true",
        "HCW_UI_TOKEN": TOKEN_FALSO,
    }
    settings = load_settings(env, base_dir=_base_dir(tmp_path))
    assert settings.ui_enabled is True
    assert settings.ui_token is not None
    assert settings.ui_token.reveal() == TOKEN_FALSO
    assert ui_enabled(settings) is True
    assert require_ui_token(settings).reveal() == TOKEN_FALSO


def test_interface_ativada_sem_token_e_rejeitada(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="HCW_UI_TOKEN"):
        load_settings({"HCW_UI_ENABLED": "true"}, base_dir=_base_dir(tmp_path))


@pytest.mark.parametrize("token", ["", "   ", "curto"])
def test_token_fraco_e_rejeitado(tmp_path: Path, token: str) -> None:
    with pytest.raises(ConfigError, match="HCW_UI_TOKEN"):
        load_settings({"HCW_UI_TOKEN": token}, base_dir=_base_dir(tmp_path))


def test_token_nao_aparece_em_texto(tmp_path: Path) -> None:
    settings = load_settings(
        {"HCW_UI_ENABLED": "true", "HCW_UI_TOKEN": TOKEN_FALSO},
        base_dir=_base_dir(tmp_path),
    )
    texto = f"{settings!r} {settings!s} {settings.ui_token!r} {settings.ui_token!s}"
    assert TOKEN_FALSO not in texto


def test_helpers_recusam_configuracao_sem_token(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    with pytest.raises(ConfigError, match="HCW_UI_TOKEN"):
        require_ui_token(settings)


def test_modulo_tem_documentacao_obrigatoria() -> None:
    root = Path(__file__).resolve().parents[2]
    package = root / "app" / "ui"
    assert (package / "README.txt").is_file()
    manifest = (package / "module.yaml").read_text(encoding="utf-8")
    for key in ("name:", "purpose:", "public_api:", "depends_on:"):
        assert key in manifest
