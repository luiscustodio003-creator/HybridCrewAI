"""Validação de caminhos confinados ao workspace."""

from __future__ import annotations

import ntpath
import os
import stat
from pathlib import Path, PureWindowsPath


class WorkspacePathError(ValueError):
    """Caminho rejeitado antes de qualquer acesso a ficheiros."""


_RESERVADOS = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{indice}" for indice in range(1, 10)}
    | {f"LPT{indice}" for indice in range(1, 10)}
)
_MIN_ASCII_IMPRIMIVEL = 32


def validate_workspace_path(
    root: Path, candidate: str | Path, *, max_chars: int
) -> Path:
    """Devolve o caminho absoluto validado, sem abrir ficheiros."""
    if max_chars < 1:
        raise WorkspacePathError("max_chars tem de ser maior que zero.")
    texto = _texto(candidate)
    raiz = _raiz_resolvida(root)
    partes = _partes(texto, max_chars)
    caminho = raiz.joinpath(*partes)
    _verificar_ligacoes(caminho, raiz)
    resolvido = _resolvido(caminho)
    if not resolvido.is_relative_to(raiz):
        raise WorkspacePathError("O caminho final sai da raiz do workspace.")
    return resolvido


def _texto(candidate: str | Path) -> str:
    """Converte o candidato sem aceitar bytes nem valores vazios."""
    valor = os.fspath(candidate)
    if isinstance(valor, bytes):
        raise WorkspacePathError("O caminho tem de ser texto ou Path, não bytes.")
    if not valor.strip():
        raise WorkspacePathError("O caminho não pode estar vazio.")
    return valor


def _raiz_resolvida(root: Path) -> Path:
    """Resolve a raiz existente antes de validar qualquer candidato."""
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise WorkspacePathError(
            "A raiz do workspace não existe ou não pode ser resolvida."
        ) from exc


def _partes(candidate: str, max_chars: int) -> tuple[str, ...]:
    """Valida o texto do caminho e devolve as suas partes relativas."""
    if len(candidate) > max_chars:
        raise WorkspacePathError(
            f"O caminho tem mais de {max_chars} caracteres; encurte-o."
        )
    windows = PureWindowsPath(candidate)
    if windows.drive or windows.root or ntpath.isabs(candidate):
        raise WorkspacePathError("O caminho não pode ser absoluto; use um caminho relativo.")
    partes = tuple(parte for parte in candidate.replace("\\", "/").split("/") if parte)
    if any(parte == ".." for parte in partes):
        raise WorkspacePathError("O caminho não pode conter travessia '..'.")
    if any(parte == "." for parte in partes):
        raise WorkspacePathError("O caminho não pode conter o componente '.'.")
    for parte in partes:
        if any(ord(caracter) < _MIN_ASCII_IMPRIMIVEL for caracter in parte):
            raise WorkspacePathError("O caminho contém caracteres de controlo.")
        if parte.endswith((".", " ")) or _e_reservado(parte):
            raise WorkspacePathError(
                f"O componente {parte!r} é reservado ou inválido no Windows."
            )
    return partes


def _e_reservado(parte: str) -> bool:
    """Detecta nomes reservados do Windows mesmo com extensão."""
    return parte.split(".", 1)[0].upper() in _RESERVADOS


def _verificar_ligacoes(caminho: Path, raiz: Path) -> None:
    """Rejeita symlinks e junctions em qualquer componente existente."""
    relativo = caminho.relative_to(raiz)
    prefixo = raiz
    for parte in relativo.parts:
        prefixo = prefixo / parte
        try:
            informacao = os.lstat(prefixo)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise WorkspacePathError(
                f"Não foi possível inspecionar {parte!r} antes da abertura."
            ) from exc
        atributos = getattr(informacao, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if prefixo.is_symlink() or bool(atributos & reparse):
            raise WorkspacePathError(
                f"O caminho contém uma ligação em {parte!r}, fora do workspace."
            )


def _resolvido(caminho: Path) -> Path:
    """Resolve o destino final sem exigir que o ficheiro exista."""
    try:
        return caminho.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise WorkspacePathError("O caminho final não pôde ser resolvido.") from exc
