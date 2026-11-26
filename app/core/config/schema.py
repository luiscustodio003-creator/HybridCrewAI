"""Esquema imutável e validado da configuração da aplicação."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config.defaults import ALLOWED_LOG_LEVELS, MIN_UI_TOKEN_CHARS
from app.core.config.secrets import SecretStr


class ConfigError(ValueError):
    """Configuração inválida; a mensagem indica como corrigi-la."""


def validate_relative_path(value: str, name: str) -> str:
    """Rejeita caminhos absolutos, vazios e travessias para fora do projecto."""
    if not value.strip():
        raise ConfigError(f"{name} não pode estar vazio; indique um caminho relativo.")
    path = Path(value)
    if path.is_absolute():
        raise ConfigError(f"{name} não pode ser um caminho absoluto: {value!r}.")
    if ".." in path.parts:
        raise ConfigError(f"{name} não pode conter '..': {value!r}.")
    return value


def validate_ollama_model(value: str) -> str:
    """Valida o nome do modelo local sem inventar valores por omissão."""
    modelo = value.strip()
    if not modelo:
        raise ConfigError(
            "HCW_OLLAMA_MODEL não pode estar vazio; indique o nome devolvido por 'ollama list'."
        )
    return modelo


def validate_ui_token(value: SecretStr) -> SecretStr:
    """Valida o comprimento do token da interface sem revelar o valor."""
    if len(value.reveal()) < MIN_UI_TOKEN_CHARS:
        raise ConfigError(
            f"HCW_UI_TOKEN tem de ter pelo menos {MIN_UI_TOKEN_CHARS} caracteres."
        )
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração validada, sem segredos e sem efeitos secundários."""

    app_name: str
    base_dir: Path
    data_dir: Path
    log_dir: Path
    event_log: Path
    sqlite_path: Path
    log_level: str
    cloud_enabled: bool
    max_file_lines: int
    ollama_model: str | None = None
    ui_enabled: bool = False
    ui_token: SecretStr | None = None
    create_flow: bool = False

    def __post_init__(self) -> None:
        """Normaliza e valida os valores após a construção."""
        if not self.app_name.strip():
            raise ConfigError("HCW_APP_NAME não pode estar vazio.")
        if not self.base_dir.is_absolute():
            raise ConfigError("base_dir tem de ser um caminho absoluto.")
        if self.log_level not in ALLOWED_LOG_LEVELS:
            allowed = ", ".join(ALLOWED_LOG_LEVELS)
            raise ConfigError(f"HCW_LOG_LEVEL inválido {self.log_level!r}; use {allowed}.")
        if self.max_file_lines < 1:
            raise ConfigError("HCW_MAX_FILE_LINES tem de ser maior que zero.")
        if self.ollama_model is not None:
            validate_ollama_model(self.ollama_model)
        if self.ui_token is not None:
            validate_ui_token(self.ui_token)
        if self.ui_enabled and self.ui_token is None:
            raise ConfigError(
                "HCW_UI_ENABLED=true exige HCW_UI_TOKEN; defina um token no ambiente."
            )
        for name, path in self._managed_paths():
            if not path.is_relative_to(self.base_dir):
                raise ConfigError(f"{name} tem de ficar dentro de {self.base_dir}.")

    def _managed_paths(self) -> tuple[tuple[str, Path], ...]:
        """Devolve os caminhos geridos, para validação de contenção."""
        return (
            ("HCW_DATA_DIR", self.data_dir),
            ("HCW_LOG_DIR", self.log_dir),
            ("HCW_EVENT_LOG", self.event_log),
            ("HCW_SQLITE_PATH", self.sqlite_path),
        )
