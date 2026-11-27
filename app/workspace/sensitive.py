"""Classificação de ficheiros sensíveis sem expor conteúdo."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.llm.egress.secret_scan import contem_segredo
from app.workspace.paths import WorkspacePathError, validate_workspace_path

_PADRAO_CHAVE_API = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
_NOMES_SENSIVEIS = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
_EXTENSOES_SENSIVEIS = (".key", ".pem", ".pfx", ".p12")


class SensitiveReason(StrEnum):
    """Motivos estáveis que tornam um ficheiro sensível."""

    FILENAME = "filename"
    CONTENT = "content"


@dataclass(frozen=True)
class SensitiveFile:
    """Metadados seguros de um ficheiro classificado."""

    path: str
    sha256: str
    size: int
    reasons: tuple[SensitiveReason, ...]

    @property
    def is_sensitive(self) -> bool:
        """Indica se o ficheiro tem pelo menos um motivo sensível."""
        return bool(self.reasons)


def classify_sensitive(
    root: Path, relative: str, *, max_chars: int, max_file_bytes: int
) -> SensitiveFile:
    """Classifica um ficheiro do workspace sem devolver conteúdo."""
    caminho = validate_workspace_path(root, relative, max_chars=max_chars)
    return inspect_sensitive_file(
        caminho, relative=relative, max_file_bytes=max_file_bytes
    )


def inspect_sensitive_file(
    path: Path, *, relative: str, max_file_bytes: int
) -> SensitiveFile:
    """Inspeciona um ficheiro local com limites e devolve apenas metadados."""
    dados, tamanho = read_attachment_bytes(path, max_file_bytes=max_file_bytes)
    return classify_bytes(
        dados, relative=relative, size=tamanho, max_file_bytes=max_file_bytes
    )


def read_attachment_bytes(path: Path, *, max_file_bytes: int) -> tuple[bytes, int]:
    """Lê um anexo regular e limitado sem seguir ligações."""
    if max_file_bytes < 1:
        raise WorkspacePathError("O limite de bytes do anexo tem de ser positivo.")
    informacao = _informacao(path)
    if _e_ligacao(path, informacao):
        raise WorkspacePathError("O ficheiro é uma ligação e não pode ser lido.")
    if not stat.S_ISREG(informacao.st_mode):
        raise WorkspacePathError("O anexo tem de ser um ficheiro regular.")
    if informacao.st_size > max_file_bytes:
        raise WorkspacePathError("O anexo excede o limite de bytes configurado.")
    dados = path.read_bytes()
    if len(dados) > max_file_bytes:
        raise WorkspacePathError("O anexo cresceu durante a leitura e foi rejeitado.")
    return dados, informacao.st_size


def classify_bytes(
    dados: bytes, *, relative: str, size: int, max_file_bytes: int
) -> SensitiveFile:
    """Classifica bytes já lidos sem guardar ou devolver o conteúdo."""
    if max_file_bytes < 1 or size > max_file_bytes or len(dados) > max_file_bytes:
        raise WorkspacePathError("O anexo excede o limite de bytes configurado.")
    texto = dados.decode("utf-8", errors="replace")
    motivos: list[SensitiveReason] = []
    if _nome_sensivel(relative):
        motivos.append(SensitiveReason.FILENAME)
    if contem_segredo(texto) or _PADRAO_CHAVE_API.search(texto):
        motivos.append(SensitiveReason.CONTENT)
    return SensitiveFile(
        path=relative.replace("\\", "/"),
        sha256=hashlib.sha256(dados).hexdigest(),
        size=size,
        reasons=tuple(motivos),
    )


def _informacao(path: Path) -> os.stat_result:
    """Obtém os atributos sem seguir ligações."""
    try:
        return os.lstat(path)
    except OSError as exc:
        raise WorkspacePathError("O anexo não pôde ser inspecionado.") from exc


def _e_ligacao(path: Path, informacao: os.stat_result) -> bool:
    """Detecta symlinks e junctions sem seguir o destino."""
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(atributos & reparse)


def _nome_sensivel(relative: str) -> bool:
    """Verifica nomes e extensões que indicam material sensível."""
    nome = Path(relative.replace("\\", "/")).name.lower()
    if nome in _NOMES_SENSIVEIS or nome.startswith(".env."):
        return True
    return nome == ".env" or nome.endswith(_EXTENSOES_SENSIVEIS)
