"""Testes da feature flag CREATE e da persona do assistente."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import ConfigError, load_settings

LIMITES_ESPERADOS = ("sem segredos", "sem execução automática")


def _base_dir(tmp_path: Path) -> Path:
    """Devolve um directório base isolado para cada teste."""
    base = tmp_path / "project"
    base.mkdir()
    return base


def test_create_flow_desligado_por_omissao(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    assert settings.create_flow is False


@pytest.mark.parametrize("valor,esperado", [("true", True), ("false", False)])
def test_create_flow_e_lido_do_ambiente(
    tmp_path: Path, valor: str, esperado: bool
) -> None:
    settings = load_settings({"HCW_CREATE_FLOW": valor}, base_dir=_base_dir(tmp_path))
    assert settings.create_flow is esperado


@pytest.mark.parametrize("valor", ["1", "sim", "yes"])
def test_create_flow_invalido_aborta_com_mensagem_clara(
    tmp_path: Path, valor: str
) -> None:
    with pytest.raises(ConfigError, match="HCW_CREATE_FLOW"):
        load_settings({"HCW_CREATE_FLOW": valor}, base_dir=_base_dir(tmp_path))


def test_persona_tem_campos_obrigatorios() -> None:
    root = Path(__file__).resolve().parents[2]
    texto = (root / "persona.md").read_text(encoding="utf-8")
    for campo in ("id:", "versao:", "tom:", "limites:"):
        assert campo in texto, f"persona.md não contém {campo}"
    for limite in LIMITES_ESPERADOS:
        assert limite in texto


def test_persona_nao_contem_segredos_nem_comandos() -> None:
    root = Path(__file__).resolve().parents[2]
    texto = (root / "persona.md").read_text(encoding="utf-8").lower()
    for proibido in ("sk-", "hcw_ui_token", "senha", "password", "subprocess", "npm "):
        assert proibido not in texto
