"""Testes da configuração carregada de variáveis de ambiente."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from app.core.config import ConfigError, load_settings
from app.core.config.defaults import MAX_FILE_LINES

if TYPE_CHECKING:
    from collections.abc import Mapping

CUSTOM_MAX_FILE_LINES = 250


def _base_dir(tmp_path: Path) -> Path:
    """Devolve um directório base isolado para cada teste."""
    base = tmp_path / "project"
    base.mkdir()
    return base


def test_valores_por_omissao_sao_seguros(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    assert settings.app_name == "HybridCrewAI"
    assert settings.log_level == "INFO"
    assert settings.cloud_enabled is False
    assert settings.max_file_lines == MAX_FILE_LINES
    assert settings.data_dir == settings.base_dir / "data"
    assert settings.log_dir == settings.base_dir / "logs"
    assert settings.ollama_model is None


def test_flags_do_workspace_sao_desligados_por_omissao(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    assert settings.workspace_write is False
    assert settings.snapshots is False
    assert settings.diff is False
    assert settings.zip_enabled is False
    assert settings.attachments is False
    assert settings.permissions is False


def test_flags_do_workspace_sao_lidas_do_ambiente(tmp_path: Path) -> None:
    env: Mapping[str, str] = {
        "HCW_WORKSPACE_WRITE": "true",
        "HCW_SNAPSHOTS": "true",
        "HCW_DIFF": "true",
        "HCW_ZIP_ENABLED": "true",
        "HCW_ATTACHMENTS": "true",
        "HCW_PERMISSIONS": "true",
    }
    settings = load_settings(env, base_dir=_base_dir(tmp_path))
    assert settings.workspace_write is True
    assert settings.snapshots is True
    assert settings.diff is True
    assert settings.zip_enabled is True
    assert settings.attachments is True
    assert settings.permissions is True


def test_limites_do_workspace_sao_positivos_por_omissao(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    limites = (
        settings.max_workspace_file_bytes,
        settings.max_workspace_path_chars,
        settings.max_zip_bytes,
        settings.max_zip_entries,
        settings.max_zip_nesting,
    )
    assert all(limite > 0 for limite in limites)


@pytest.mark.parametrize(
    "chave",
    [
        "HCW_MAX_WORKSPACE_FILE_BYTES",
        "HCW_MAX_WORKSPACE_PATH_CHARS",
        "HCW_MAX_ZIP_BYTES",
        "HCW_MAX_ZIP_ENTRIES",
        "HCW_MAX_ZIP_NESTING",
    ],
)
def test_limite_do_workspace_zero_e_rejeitado(tmp_path: Path, chave: str) -> None:
    with pytest.raises(ConfigError, match=chave):
        load_settings({chave: "0"}, base_dir=_base_dir(tmp_path))


@pytest.mark.parametrize("valor", ["-1", "300;rm -rf /"])
def test_limite_do_workspace_invalido_aborta_sem_executar_texto(
    tmp_path: Path, valor: str
) -> None:
    with pytest.raises(ConfigError, match="HCW_MAX_ZIP_BYTES"):
        load_settings({"HCW_MAX_ZIP_BYTES": valor}, base_dir=_base_dir(tmp_path))


@pytest.mark.parametrize(
    "chave",
    [
        "HCW_WORKSPACE_WRITE",
        "HCW_SNAPSHOTS",
        "HCW_DIFF",
        "HCW_ZIP_ENABLED",
        "HCW_ATTACHMENTS",
        "HCW_PERMISSIONS",
    ],
)
def test_flag_do_workspace_invalida_e_rejeitada(tmp_path: Path, chave: str) -> None:
    with pytest.raises(ConfigError, match=chave):
        load_settings({chave: "sim"}, base_dir=_base_dir(tmp_path))


def test_workspace_fica_dentro_do_directorio_de_dados(tmp_path: Path) -> None:
    settings = load_settings({}, base_dir=_base_dir(tmp_path))
    assert settings.workspace_dir.parent == settings.data_dir
    assert settings.workspace_dir.is_relative_to(settings.base_dir)


def test_variavel_desconhecida_nao_altera_o_workspace(tmp_path: Path) -> None:
    base = _base_dir(tmp_path)
    externo = base.parent / "fora"
    settings = load_settings({"HCW_WORKSPACE_DIR": str(externo)}, base_dir=base)
    assert settings.workspace_dir == base / "data" / "workspace"
    assert settings.workspace_dir.is_relative_to(base)


def test_variaveis_de_ambiente_sobrescrevem_omissoes(tmp_path: Path) -> None:
    base = _base_dir(tmp_path)
    env: Mapping[str, str] = {
        "HCW_LOG_LEVEL": "warning",
        "HCW_CLOUD_ENABLED": "true",
        "HCW_MAX_FILE_LINES": str(CUSTOM_MAX_FILE_LINES),
        "HCW_DATA_DIR": "estado",
    }
    settings = load_settings(env, base_dir=base)
    assert settings.log_level == "WARNING"
    assert settings.cloud_enabled is True
    assert settings.max_file_lines == CUSTOM_MAX_FILE_LINES
    assert settings.data_dir == base / "estado"


def test_modelo_ollama_e_lido_da_configuracao(tmp_path: Path) -> None:
    settings = load_settings({"HCW_OLLAMA_MODEL": "modelo-local"}, base_dir=_base_dir(tmp_path))
    assert settings.ollama_model == "modelo-local"


@pytest.mark.parametrize("valor", ["", "   "])
def test_modelo_ollama_vazio_e_rejeitado(tmp_path: Path, valor: str) -> None:
    with pytest.raises(ConfigError, match="HCW_OLLAMA_MODEL"):
        load_settings({"HCW_OLLAMA_MODEL": valor}, base_dir=_base_dir(tmp_path))


@pytest.mark.parametrize("valor", ["TRACE", "", "VERBOSE"])
def test_nivel_de_log_invalido_aborta_com_mensagem_clara(tmp_path: Path, valor: str) -> None:
    with pytest.raises(ConfigError, match="HCW_LOG_LEVEL"):
        load_settings({"HCW_LOG_LEVEL": valor}, base_dir=_base_dir(tmp_path))


@pytest.mark.parametrize("valor", ["sim", "1", "yes"])
def test_booleano_invalido_aborta(tmp_path: Path, valor: str) -> None:
    with pytest.raises(ConfigError, match="HCW_CLOUD_ENABLED"):
        load_settings({"HCW_CLOUD_ENABLED": valor}, base_dir=_base_dir(tmp_path))


def test_inteiro_invalido_aborta_sem_executar_texto(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="HCW_MAX_FILE_LINES"):
        load_settings({"HCW_MAX_FILE_LINES": "300;rm -rf /"}, base_dir=_base_dir(tmp_path))


def test_caminho_absoluto_e_rejeitado(tmp_path: Path) -> None:
    externo = tmp_path / "fora"
    with pytest.raises(ConfigError, match="absoluto"):
        load_settings({"HCW_DATA_DIR": str(externo)}, base_dir=_base_dir(tmp_path))


def test_traversal_e_rejeitado(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"\.\."):
        load_settings({"HCW_LOG_DIR": r"..\externo"}, base_dir=_base_dir(tmp_path))


def test_chave_de_api_nao_faz_parte_da_configuracao(tmp_path: Path) -> None:
    settings = load_settings({"HCW_API_KEY": "sk-TEST-NAO-GRAVAR"}, base_dir=_base_dir(tmp_path))
    assert not hasattr(settings, "api_key")
    assert "sk-TEST-NAO-GRAVAR" not in repr(settings)


def test_carregar_configuracao_nao_escreve_ficheiros(tmp_path: Path) -> None:
    base = _base_dir(tmp_path)
    settings = load_settings({}, base_dir=base)
    assert list(base.iterdir()) == []
    assert settings.event_log == base / "logs" / "events.jsonl"


def test_modulo_usa_apenas_biblioteca_padrao() -> None:
    root = Path(__file__).resolve().parents[2]
    package = root / "app" / "core" / "config"
    permitidos = {
        "__future__",
        "app",
        "collections",
        "dataclasses",
        "os",
        "pathlib",
        "re",
        "typing",
    }
    for source in package.glob("*.py"):
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.startswith(("import ", "from ")):
                modulo = line.split()[1].split(".")[0]
                assert modulo in permitidos, f"{source.name}: importação externa {modulo}"


def test_pyproject_inclui_app_na_analise() -> None:
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'src = ["app", "scripts", "tests"]' in pyproject
    assert 'known-first-party = ["app", "scripts"]' in pyproject


def test_modulo_tem_documentacao_obrigatoria() -> None:
    root = Path(__file__).resolve().parents[2]
    package = root / "app" / "core" / "config"
    assert (package / "README.txt").is_file()
    manifest = (package / "module.yaml").read_text(encoding="utf-8")
    for key in ("name:", "purpose:", "public_api:", "depends_on:"):
        assert key in manifest
