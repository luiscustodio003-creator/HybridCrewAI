"""Carregamento da configuração a partir de variáveis de ambiente."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from app.core.config.defaults import (
    APP_NAME,
    CLOUD_ENABLED,
    CREATE_FLOW,
    DATA_DIR,
    ENV_PREFIX,
    EVENT_LOG,
    LOG_DIR,
    LOG_LEVEL,
    MAX_FILE_LINES,
    OLLAMA_MODEL,
    SQLITE_PATH,
    UI_ENABLED,
    UI_TOKEN,
)
from app.core.config.schema import (
    ConfigError,
    Settings,
    validate_ollama_model,
    validate_relative_path,
    validate_ui_token,
)
from app.core.config.secrets import SecretStr


def _text_value(environ: Mapping[str, str], key: str, default: str) -> str:
    """Lê um valor textual com o prefixo HCW_."""
    return environ.get(f"{ENV_PREFIX}{key}", default)


def _bool_value(environ: Mapping[str, str], key: str, default: bool) -> bool:
    """Converte um valor booleano explícito, sem aceitar atalhos ambíguos."""
    text = _text_value(environ, key, "true" if default else "false").strip().lower()
    if text in {"true", "false"}:
        return text == "true"
    raise ConfigError(f"{ENV_PREFIX}{key} tem de ser true ou false; recebido {text!r}.")


def _int_value(environ: Mapping[str, str], key: str, default: int) -> int:
    """Converte um inteiro sem interpretar ou executar o texto recebido."""
    text = _text_value(environ, key, str(default)).strip()
    try:
        return int(text)
    except ValueError as exc:
        raise ConfigError(f"{ENV_PREFIX}{key} tem de ser um inteiro; recebido {text!r}.") from exc


def _path_value(environ: Mapping[str, str], key: str, default: str, base_dir: Path) -> Path:
    """Resolve um caminho relativo dentro do directório base."""
    relative = validate_relative_path(_text_value(environ, key, default), f"{ENV_PREFIX}{key}")
    return (base_dir / relative).resolve()


def _secret_value(environ: Mapping[str, str], key: str, default: str | None) -> SecretStr | None:
    """Lê um segredo do ambiente sem o gravar nem revelar em mensagens."""
    valor = environ.get(f"{ENV_PREFIX}{key}", default)
    if valor is None:
        return None
    if not valor.strip():
        raise ConfigError(f"{ENV_PREFIX}{key} não pode estar vazio; defina um valor no ambiente.")
    return validate_ui_token(SecretStr(valor))


def _model_value(environ: Mapping[str, str]) -> str | None:
    """Lê o modelo local sem aplicar nomes por omissão."""
    valor = environ.get(f"{ENV_PREFIX}OLLAMA_MODEL", OLLAMA_MODEL)
    return None if valor is None else validate_ollama_model(valor)


def load_settings(
    environ: Mapping[str, str] | None = None,
    base_dir: Path | None = None,
) -> Settings:
    """Carrega e valida a configuração sem gravar ficheiros nem revelar segredos."""
    environment = os.environ if environ is None else environ
    root = (base_dir or Path(__file__).resolve().parents[3]).resolve()
    level = _text_value(environment, "LOG_LEVEL", LOG_LEVEL).strip().upper()
    return Settings(
        app_name=_text_value(environment, "APP_NAME", APP_NAME).strip(),
        base_dir=root,
        data_dir=_path_value(environment, "DATA_DIR", DATA_DIR, root),
        log_dir=_path_value(environment, "LOG_DIR", LOG_DIR, root),
        event_log=_path_value(environment, "EVENT_LOG", EVENT_LOG, root),
        sqlite_path=_path_value(environment, "SQLITE_PATH", SQLITE_PATH, root),
        log_level=level,
        cloud_enabled=_bool_value(environment, "CLOUD_ENABLED", CLOUD_ENABLED),
        max_file_lines=_int_value(environment, "MAX_FILE_LINES", MAX_FILE_LINES),
        ollama_model=_model_value(environment),
        ui_enabled=_bool_value(environment, "UI_ENABLED", UI_ENABLED),
        ui_token=_secret_value(environment, "UI_TOKEN", UI_TOKEN),
        create_flow=_bool_value(environment, "CREATE_FLOW", CREATE_FLOW),
    )
