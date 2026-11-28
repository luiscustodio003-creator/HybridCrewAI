"""Contrato e validação dos pedidos de anexos."""

from __future__ import annotations

import base64
import binascii
import hmac
import json
import re
import zipfile
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from typing import Final

from approvals.tokens import (
    ApprovalDenied,
    ApprovalError,
    ApprovalToken,
    TokenStore,
    hash_diff_obrigatorio,
    texto_obrigatorio,
)

from app.ui.server.routes_chat import MAX_CORPO_BYTES
from app.workspace import ArchiveError, QuarantineError, WorkspacePathError

ATTACHMENTS_PATH: Final = "/api/attachments"
RELEASE_PATH: Final = "/api/attachments/release"
CAMPOS_UPLOAD: Final = frozenset(
    {
        "task_id",
        "correlation_id",
        "diff_hash",
        "approval_token",
        "filename",
        "content_base64",
    }
)
CAMPOS_RELEASE: Final = frozenset(
    {
        "attachment_id",
        "task_id",
        "correlation_id",
        "diff_hash",
        "approval_token",
    }
)
_MAGICOS_ZIP: Final = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_NOME_ZIP: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.zip")
_ID_ANEXO: Final = re.compile(r"[0-9a-f]{32}")


@dataclass(frozen=True, slots=True)
class Upload:
    """Pedido de upload já validado e ligado a uma aprovação."""

    task_id: str
    correlation_id: str
    diff_hash: str
    approval_token: str
    filename: str
    dados: bytes


@dataclass(frozen=True, slots=True)
class Release:
    """Pedido de libertação já validado e ligado a uma aprovação."""

    attachment_id: str
    task_id: str
    correlation_id: str
    diff_hash: str
    approval_token: str


ERROS = (
    ValueError,
    ApprovalError,
    QuarantineError,
    ArchiveError,
    WorkspacePathError,
    binascii.Error,
    zipfile.BadZipFile,
    OSError,
)


def limite_corpo(caminho: str, max_zip_bytes: int) -> int:
    """Devolve o limite do corpo para a rota de anexos pedida."""
    if caminho == RELEASE_PATH:
        return MAX_CORPO_BYTES
    return max_zip_bytes * 2 + MAX_CORPO_BYTES


def ler_corpo(handler: BaseHTTPRequestHandler, limite: int) -> bytes:
    """Lê um corpo obrigatório e limitado antes de qualquer parsing."""
    try:
        tamanho = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise ValueError("Content-Length inválido.") from exc
    if not 0 < tamanho <= limite:
        raise ValueError("O corpo do pedido é obrigatório e está limitado.")
    return handler.rfile.read(tamanho)


def _json(corpo: bytes, campos: frozenset[str]) -> dict[str, object]:
    """Lê JSON estrito, sem campos desconhecidos nem valores não objecto."""
    try:
        dados = json.loads(corpo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Corpo JSON inválido.") from exc
    if not isinstance(dados, dict) or set(dados) != campos:
        raise ValueError("O corpo contém campos inesperados ou em falta.")
    return dados


def analisar_upload(corpo: bytes) -> Upload:
    """Valida os campos de upload e devolve os bytes do ZIP."""
    dados = _json(corpo, CAMPOS_UPLOAD)
    nome = texto_obrigatorio(dados["filename"], "filename")
    if _NOME_ZIP.fullmatch(nome) is None:
        raise ValueError("O nome do anexo tem de ser um ficheiro .zip simples.")
    texto = dados["content_base64"]
    if not isinstance(texto, str) or not texto:
        raise ValueError("O campo content_base64 é obrigatório.")
    try:
        conteudo = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("O conteúdo base64 é inválido.") from exc
    if not conteudo:
        raise ValueError("O anexo não pode estar vazio.")
    return Upload(
        task_id=texto_obrigatorio(dados["task_id"], "task_id"),
        correlation_id=texto_obrigatorio(dados["correlation_id"], "correlation_id"),
        diff_hash=hash_diff_obrigatorio(dados["diff_hash"]),
        approval_token=texto_obrigatorio(dados["approval_token"], "approval_token"),
        filename=nome,
        dados=conteudo,
    )


def analisar_release(corpo: bytes) -> Release:
    """Valida os campos de libertação e o identificador do anexo."""
    dados = _json(corpo, CAMPOS_RELEASE)
    identificador = texto_obrigatorio(dados["attachment_id"], "attachment_id")
    if _ID_ANEXO.fullmatch(identificador) is None:
        raise ValueError("O identificador do anexo é inválido.")
    return Release(
        attachment_id=identificador,
        task_id=texto_obrigatorio(dados["task_id"], "task_id"),
        correlation_id=texto_obrigatorio(dados["correlation_id"], "correlation_id"),
        diff_hash=hash_diff_obrigatorio(dados["diff_hash"]),
        approval_token=texto_obrigatorio(dados["approval_token"], "approval_token"),
    )


def validar_aprovacao(
    tokens: TokenStore, pedido: Upload | Release
) -> ApprovalToken:
    """Exige token válido para a tarefa, diff e correlação apresentados."""
    registro = tokens.validar(pedido.approval_token, pedido.task_id, pedido.diff_hash)
    if not hmac.compare_digest(registro.correlation_id, pedido.correlation_id):
        raise ValueError("A correlação não corresponde à aprovação.")
    return registro


__all__ = [
    "ATTACHMENTS_PATH",
    "RELEASE_PATH",
    "ERROS",
    "ApprovalDenied",
    "Upload",
    "Release",
    "analisar_release",
    "analisar_upload",
    "ler_corpo",
    "limite_corpo",
    "validar_aprovacao",
]
