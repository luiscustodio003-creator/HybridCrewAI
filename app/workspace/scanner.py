"""Scanner de cobertura do workspace."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path


class IgnoreReason(StrEnum):
    """Motivos estáveis para um ficheiro não ser lido."""

    LINK = "link"
    INVALID_PATH = "invalid-path"
    TOO_LARGE = "too-large"
    NOT_REGULAR = "not-regular"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class IgnoredFile:
    """Ficheiro não lido e motivo estável da exclusão."""

    path: str
    reason: IgnoreReason


@dataclass(frozen=True)
class WorkspaceScan:
    """Resultado da cobertura do workspace."""

    root: Path
    readable: tuple[str, ...]
    ignored: tuple[IgnoredFile, ...]
    directories_ignored: tuple[IgnoredFile, ...]
    total_on_disk: int

    @property
    def total_classified(self) -> int:
        """Devolve a soma de ficheiros lidos e ignorados."""
        return len(self.readable) + len(self.ignored)

    @property
    def coverage_complete(self) -> bool:
        """Indica se a soma cobre todos os ficheiros listados."""
        return self.total_classified == self.total_on_disk


def scan_workspace(
    root: Path, *, max_chars: int, max_file_bytes: int
) -> WorkspaceScan:
    """Lista o workspace sem ler conteúdos nem seguir ligações externas."""
    if max_chars < 1 or max_file_bytes < 1:
        raise WorkspacePathError("Os limites do workspace têm de ser positivos.")
    raiz = _validar_raiz(root)
    legiveis: list[str] = []
    ignorados: list[IgnoredFile] = []
    diretorios: list[IgnoredFile] = []

    def registrar_erro(erro: OSError) -> None:
        diretorios.append(_ignorado_por_erro(raiz, erro))

    total = 0
    for atual, nomes_dir, nomes_ficheiro in os.walk(raiz, onerror=registrar_erro):
        _filtrar_diretorios(raiz, Path(atual), nomes_dir, diretorios)
        nomes_dir.sort()
        for nome in sorted(nomes_ficheiro):
            total += 1
            relativo = _relativo(raiz, Path(atual) / nome)
            motivo = _motivo_ignorado(raiz, relativo, max_chars, max_file_bytes)
            if motivo is None:
                legiveis.append(relativo)
            else:
                ignorados.append(IgnoredFile(relativo, motivo))
    return WorkspaceScan(
        root=raiz,
        readable=tuple(legiveis),
        ignored=tuple(ignorados),
        directories_ignored=tuple(diretorios),
        total_on_disk=total,
    )


def _validar_raiz(root: Path) -> Path:
    """Confirma que a raiz é uma directoria real e sem ligações."""
    try:
        informacao = os.lstat(root)
    except OSError as exc:
        raise WorkspacePathError(
            "A raiz do workspace não existe ou não pode ser lida."
        ) from exc
    if _e_ligacao(root, informacao):
        raise WorkspacePathError("A raiz do workspace não pode ser uma ligação.")
    if not stat.S_ISDIR(informacao.st_mode):
        raise WorkspacePathError("A raiz do workspace tem de ser uma directoria.")
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise WorkspacePathError("A raiz do workspace não pôde ser resolvida.") from exc


def _filtrar_diretorios(
    root: Path,
    atual: Path,
    nomes: list[str],
    destino: list[IgnoredFile],
) -> None:
    """Remove diretorias ligadas ou ilegíveis antes de as percorrer."""
    for nome in list(nomes):
        caminho = atual / nome
        relativo = _relativo(root, caminho)
        try:
            informacao = os.lstat(caminho)
        except OSError:
            destino.append(IgnoredFile(relativo, IgnoreReason.UNREADABLE))
            nomes.remove(nome)
            continue
        if _e_ligacao(caminho, informacao):
            destino.append(IgnoredFile(relativo, IgnoreReason.LINK))
            nomes.remove(nome)


def _motivo_ignorado(
    root: Path, relativo: str, max_chars: int, max_file_bytes: int
) -> IgnoreReason | None:
    """Devolve o motivo estável da exclusão ou None se o ficheiro for legível."""
    caminho = root.joinpath(*relativo.split("/"))
    try:
        informacao = os.lstat(caminho)
    except OSError:
        return IgnoreReason.UNREADABLE
    if _e_ligacao(caminho, informacao):
        return IgnoreReason.LINK
    try:
        validate_workspace_path(root, relativo, max_chars=max_chars)
    except WorkspacePathError:
        return IgnoreReason.INVALID_PATH
    if not stat.S_ISREG(informacao.st_mode):
        return IgnoreReason.NOT_REGULAR
    if informacao.st_size > max_file_bytes:
        return IgnoreReason.TOO_LARGE
    return None


def _ignorado_por_erro(root: Path, erro: OSError) -> IgnoredFile:
    """Converte um erro de percurso numa entrada ignorada estável."""
    original = erro.filename
    if original is None:
        return IgnoredFile(".", IgnoreReason.UNREADABLE)
    texto = os.fsdecode(original) if isinstance(original, bytes) else original
    return IgnoredFile(_relativo(root, Path(texto)), IgnoreReason.UNREADABLE)


def _e_ligacao(caminho: Path, informacao: os.stat_result) -> bool:
    """Detecta symlinks e junctions sem seguir o destino."""
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return caminho.is_symlink() or bool(atributos & reparse)


def _relativo(root: Path, caminho: Path) -> str:
    """Devolve o caminho relativo normalizado com separadores '/'."""
    try:
        return caminho.relative_to(root).as_posix()
    except ValueError:
        return caminho.name
