"""Quarentena de anexos até aprovação explícita."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.sensitive import (
    SensitiveReason,
    classify_bytes,
    read_attachment_bytes,
)

_QUARANTINE_DIR = ".quarantine"


class QuarantineError(ValueError):
    """Anexo rejeitado ou aprovação inválida."""


@dataclass(frozen=True)
class QuarantineLimits:
    """Limites de caminho e tamanho aplicados aos anexos."""

    max_chars: int
    max_file_bytes: int


@dataclass(frozen=True)
class QuarantinedAttachment:
    """Registo seguro de um anexo retido em quarentena."""

    id: str
    quarantined_path: str
    destination_path: str
    sha256: str
    size: int
    reasons: tuple[SensitiveReason, ...]
    approval_digest: str


def quarantine_attachment(
    root: Path,
    source: Path,
    *,
    relative_name: str,
    approval_token: str,
    limits: QuarantineLimits,
) -> QuarantinedAttachment:
    """Copia um anexo para quarentena sem o tornar disponível no workspace."""
    if not approval_token.strip():
        raise QuarantineError("A aprovação tem de usar um token opaco não vazio.")
    raiz = _validar_raiz(root)
    destino_rel = _destino_relativo(raiz, relative_name, limits.max_chars)
    try:
        dados, tamanho = read_attachment_bytes(
            source, max_file_bytes=limits.max_file_bytes
        )
    except WorkspacePathError as exc:
        raise QuarantineError("O anexo não pôde ser lido para quarentena.") from exc
    classificado = classify_bytes(
        dados,
        relative=destino_rel,
        size=tamanho,
        max_file_bytes=limits.max_file_bytes,
    )
    diretorio = _preparar_diretorio(raiz / _QUARANTINE_DIR)
    ident = uuid.uuid4().hex
    nome = f"{ident}.bin"
    caminho = diretorio / nome
    digest = _copiar(caminho, dados)
    if digest != classificado.sha256:
        caminho.unlink(missing_ok=True)
        raise QuarantineError("A cópia em quarentena falhou a verificação de hash.")
    registro = QuarantinedAttachment(
        id=ident,
        quarantined_path=f"{_QUARANTINE_DIR}/{nome}",
        destination_path=destino_rel,
        sha256=classificado.sha256,
        size=classificado.size,
        reasons=classificado.reasons,
        approval_digest=_token_digest(approval_token),
    )
    _guardar_metadados(diretorio / f"{ident}.json", registro)
    return registro


def release_quarantine(
    root: Path, record_id: str, *, approval_token: str, limits: QuarantineLimits
) -> Path:
    """Liberta um anexo para o workspace só com o token de aprovação correcto."""
    if not approval_token.strip() or not record_id.strip():
        raise QuarantineError("O identificador e a aprovação são obrigatórios.")
    raiz = _validar_raiz(root)
    metadados, caminho_metadados = _carregar_metadados(
        raiz, record_id, limits.max_chars
    )
    if not hmac.compare_digest(
        _token_digest(approval_token), str(metadados["approval_digest"])
    ):
        raise QuarantineError("A aprovação não autoriza este anexo.")
    origem = validate_workspace_path(
        raiz, str(metadados["quarantined_path"]), max_chars=limits.max_chars
    )
    destino = validate_workspace_path(
        raiz, str(metadados["destination_path"]), max_chars=limits.max_chars
    )
    if destino.exists():
        raise QuarantineError("O destino do anexo já existe; escolha outro nome.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    origem.replace(destino)
    if _hash_ficheiro(destino) != str(metadados["sha256"]):
        raise QuarantineError("O anexo libertado falhou a verificação de hash.")
    caminho_metadados.unlink(missing_ok=True)
    return destino


def _validar_raiz(root: Path) -> Path:
    """Confirma uma raiz real e sem ligações antes de qualquer escrita."""
    try:
        informacao = os.lstat(root)
    except OSError as exc:
        raise QuarantineError("A raiz do workspace não existe ou não pode ser lida.") from exc
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if root.is_symlink() or bool(atributos & reparse):
        raise QuarantineError("A raiz do workspace não pode ser uma ligação.")
    if not stat.S_ISDIR(informacao.st_mode):
        raise QuarantineError("A raiz do workspace tem de ser uma directoria.")
    try:
        return root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise QuarantineError("A raiz do workspace não pôde ser resolvida.") from exc


def _destino_relativo(root: Path, relative_name: str, max_chars: int) -> str:
    """Valida o destino final e devolve o seu caminho relativo normalizado."""
    destino = validate_workspace_path(root, relative_name, max_chars=max_chars)
    return destino.relative_to(root).as_posix()


def _preparar_diretorio(diretorio: Path) -> Path:
    """Cria ou valida a pasta de quarentena sem seguir ligações."""
    try:
        informacao = os.lstat(diretorio)
    except FileNotFoundError:
        diretorio.mkdir(parents=True)
        return diretorio
    except OSError as exc:
        raise QuarantineError("A pasta de quarentena não pôde ser lida.") from exc
    atributos = getattr(informacao, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if diretorio.is_symlink() or bool(atributos & reparse) or not stat.S_ISDIR(informacao.st_mode):
        raise QuarantineError("A pasta de quarentena não é uma directoria segura.")
    return diretorio


def _copiar(destino: Path, dados: bytes) -> str:
    """Escreve os bytes uma única vez e devolve o SHA-256 copiado."""
    digest = hashlib.sha256()
    try:
        with destino.open("xb") as ficheiro:
            ficheiro.write(dados)
            digest.update(dados)
    except OSError as exc:
        raise QuarantineError("Não foi possível gravar o anexo em quarentena.") from exc
    return digest.hexdigest()


def _hash_ficheiro(caminho: Path) -> str:
    """Calcula o SHA-256 de um ficheiro já validado."""
    try:
        return hashlib.sha256(caminho.read_bytes()).hexdigest()
    except OSError as exc:
        raise QuarantineError("Não foi possível verificar o anexo libertado.") from exc


def _token_digest(token: str) -> str:
    """Produz um digest do token sem guardar o token em texto."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _guardar_metadados(caminho: Path, registro: QuarantinedAttachment) -> None:
    """Grava apenas metadados verificáveis, nunca conteúdo nem token."""
    conteudo = {
        "id": registro.id,
        "quarantined_path": registro.quarantined_path,
        "destination_path": registro.destination_path,
        "sha256": registro.sha256,
        "size": registro.size,
        "reasons": [motivo.value for motivo in registro.reasons],
        "approval_digest": registro.approval_digest,
    }
    try:
        with caminho.open("x", encoding="utf-8") as ficheiro:
            json.dump(conteudo, ficheiro, ensure_ascii=False, sort_keys=True)
    except OSError as exc:
        raise QuarantineError("Não foi possível gravar os metadados do anexo.") from exc


def _carregar_metadados(
    root: Path, record_id: str, max_chars: int
) -> tuple[dict[str, object], Path]:
    """Lê e valida os metadados de um registo de quarentena."""
    relativo = f"{_QUARANTINE_DIR}/{record_id}.json"
    try:
        caminho = validate_workspace_path(root, relativo, max_chars=max_chars)
        with caminho.open("r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)
    except (OSError, ValueError, WorkspacePathError) as exc:
        raise QuarantineError("O registo de quarentena não pôde ser lido.") from exc
    obrigatorios = (
        "quarantined_path",
        "destination_path",
        "sha256",
        "approval_digest",
    )
    if any(not isinstance(dados.get(chave), str) for chave in obrigatorios):
        raise QuarantineError("O registo de quarentena está incompleto.")
    return dados, caminho
