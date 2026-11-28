"""Caminhos, limites e validação de ZIP dos anexos."""

from __future__ import annotations

import io
import stat
import uuid
import zipfile
from pathlib import Path
from typing import Final

from app.core.config import Settings
from app.ui.server.attachments_contract import _MAGICOS_ZIP
from app.workspace import ArchiveLimits, QuarantineLimits, validate_workspace_path

_STAGING: Final = ".archive-staging"
_FATOR_TOTAL: Final = 10
_RATIO_MAX: Final = 10
_MODO_ESPECIAL: Final = 0o170000
_TIPOS_ESPECIAIS: Final = frozenset(
    {
        stat.S_IFLNK,
        stat.S_IFBLK,
        stat.S_IFCHR,
        stat.S_IFIFO,
        stat.S_IFSOCK,
    }
)


def raiz(settings: Settings) -> Path:
    """Cria e valida a raiz do workspace antes de qualquer escrita."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    relativo = settings.workspace_dir.relative_to(settings.base_dir).as_posix()
    caminho = validate_workspace_path(
        settings.base_dir, relativo, max_chars=settings.max_workspace_path_chars
    )
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def limites_quarentena(settings: Settings) -> QuarantineLimits:
    """Aplica limites de caminho e tamanho ao ficheiro ZIP em quarentena."""
    return QuarantineLimits(
        max_chars=settings.max_workspace_path_chars,
        max_file_bytes=settings.max_zip_bytes,
    )


def limites_extracao(settings: Settings) -> ArchiveLimits:
    """Aplica limites de extração antes de confiar no conteúdo do ZIP."""
    return ArchiveLimits(
        max_chars=settings.max_workspace_path_chars,
        max_file_bytes=settings.max_zip_bytes,
        max_total_bytes=settings.max_zip_bytes * _FATOR_TOTAL,
        max_zip_bytes=settings.max_zip_bytes,
        max_entries=settings.max_zip_entries,
        max_ratio=_RATIO_MAX,
        max_nesting=settings.max_zip_nesting,
    )


def validar_zip(dados: bytes, caminho: Path, settings: Settings) -> None:
    """Valida entradas, limites e caminhos antes de criar quarentena."""
    if dados[:4] not in _MAGICOS_ZIP:
        raise ValueError("O anexo não é um ZIP reconhecido.")
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as arquivo:
            entradas = arquivo.infolist()
            if not entradas or len(entradas) > settings.max_zip_entries:
                raise ValueError("O ZIP não tem entradas ou tem demasiadas.")
            total = 0
            for entrada in entradas:
                total += _validar_entrada(arquivo, entrada, caminho, settings)
                if total > settings.max_zip_bytes * _FATOR_TOTAL:
                    raise ValueError("O ZIP excede o tamanho total permitido.")
    except (RuntimeError, EOFError, NotImplementedError, OSError) as exc:
        raise ValueError("Não foi possível ler o ZIP recebido.") from exc


def _validar_entrada(
    arquivo: zipfile.ZipFile,
    entrada: zipfile.ZipInfo,
    caminho: Path,
    settings: Settings,
) -> int:
    """Valida uma entrada do ZIP devolvendo o tamanho descomprimido."""
    if entrada.flag_bits & 0x1:
        raise ValueError("O ZIP contém uma entrada encriptada.")
    modo = (entrada.external_attr >> 16) & _MODO_ESPECIAL
    if modo in _TIPOS_ESPECIAIS:
        raise ValueError("O ZIP contém uma ligação ou ficheiro especial.")
    validate_workspace_path(
        caminho, entrada.filename, max_chars=settings.max_workspace_path_chars
    )
    if entrada.is_dir():
        return 0
    if entrada.file_size > settings.max_zip_bytes:
        raise ValueError("Uma entrada do ZIP excede o limite de bytes.")
    if entrada.file_size > max(1, entrada.compress_size) * _RATIO_MAX:
        raise ValueError("O ZIP excede o rácio de compressão permitido.")
    conteudo = arquivo.read(entrada)
    if len(conteudo) != entrada.file_size:
        raise ValueError("O tamanho declarado da entrada não corresponde aos dados.")
    nome = entrada.filename.replace("\\", "/")
    nivel = sum(parte.lower().endswith(".zip") for parte in nome.split("/")) + 1
    if nivel > settings.max_zip_nesting and conteudo[:4] in _MAGICOS_ZIP:
        raise ValueError("O ZIP excede o nível de aninhamento permitido.")
    return entrada.file_size


def gravar_staging(
    raiz: Path, settings: Settings, nome: str, dados: bytes
) -> Path:
    """Grava um ZIP temporário dentro do workspace para quarentena."""
    relativo = f"{_STAGING}/{uuid.uuid4().hex}/{nome}"
    destino = validate_workspace_path(
        raiz, relativo, max_chars=settings.max_workspace_path_chars
    )
    destino.parent.mkdir(parents=True)
    destino.write_bytes(dados)
    return destino


__all__ = [
    "gravar_staging",
    "limites_extracao",
    "limites_quarentena",
    "raiz",
    "validar_zip",
]
