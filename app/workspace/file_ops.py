"""Escritas atómicas por etapa e recuperação de operações interrompidas."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

from app.core.events import EventContext, EventLevel
from app.workspace import journal
from app.workspace.audit import AuditError, AuditTrail
from app.workspace.journal import (
    FileChange,
    FileOpLimits,
    FileOpReport,
    FileOpsError,
    RecoveryReport,
)
from app.workspace.paths import WorkspacePathError, validate_workspace_path


def apply_atomic(
    root: Path,
    changes: Iterable[FileChange],
    *,
    context: EventContext,
    audit: AuditTrail,
    limits: FileOpLimits,
) -> FileOpReport:
    """Prepara, confirma e aplica um grupo de escritas no workspace."""
    journal.validar_limites(limits)
    raiz = journal.raiz_segura(root)
    previstos = _validar_alteracoes(raiz, changes, limits)
    operacao = os.urandom(16).hex()
    manifesto = journal.novo_manifest(raiz, operacao, previstos, limits)
    confirmado = False
    try:
        staging = journal.preparar_staging(raiz, operacao, limits)
        _gravar_staging(staging, previstos, limits)
        pendente = journal.caminho_interno(
            raiz, f"{journal.DIRETORIO}/{journal.PENDING}/{operacao}.json", limits
        )
        journal.gravar_json(pendente, manifesto, raiz, limits)
        _registar(
            audit,
            context,
            "workspace.pending",
            "Escrita preparada para commit.",
            {"operation_id": operacao, "sha256": manifesto["digest"]},
        )
        _registar_commit(raiz, operacao, limits)
        confirmado = True
        _aplicar_manifest((raiz, staging), manifesto, context, audit, limits)
    except FileOpsError:
        raise
    except Exception as exc:
        if confirmado:
            _registar(
                audit,
                context,
                "workspace.interrupted",
                "Escrita confirmada; recuperação pendente.",
                {"operation_id": operacao, "sha256": manifesto["digest"]},
            )
            raise FileOpsError(
                "A escrita foi confirmada; execute recover_workspace para a concluir."
            ) from exc
        _registar(
            audit,
            context,
            "workspace.failed",
            "Escrita rejeitada antes do commit.",
            {"operation_id": operacao, "sha256": manifesto["digest"]},
        )
        raise FileOpsError(
            "A escrita não pôde ser concluída; nenhum ficheiro foi alterado."
        ) from exc
    journal.limpar_operacao(raiz, operacao, limits)
    return FileOpReport(
        operacao,
        str(manifesto["digest"]),
        tuple(
            str(item["path"])
            for item in cast("Sequence[Mapping[str, object]]", manifesto["files"])
        ),
    )


def recover_workspace(
    root: Path,
    *,
    context: EventContext,
    audit: AuditTrail,
    limits: FileOpLimits,
) -> RecoveryReport:
    """Completa commits confirmados e descarta preparações sem commit."""
    journal.validar_limites(limits)
    raiz = journal.raiz_segura(root)
    confirmados = journal.listar_manifestos(raiz, journal.COMMITTED, limits)
    operacoes: list[str] = []
    restaurados = 0
    for caminho, manifesto in confirmados:
        operacao = str(manifesto["operation_id"])
        staging = journal.caminho_interno(
            raiz, f"{journal.DIRETORIO}/{journal.STAGING}/{operacao}", limits
        )
        if not staging.is_dir():
            raise FileOpsError(
                "O staging da operação confirmada desapareceu; restaure o snapshot anterior."
            )
        restaurados += _aplicar_manifest(
            (raiz, staging), manifesto, context, audit, limits
        )
        operacoes.append(operacao)
        caminho.unlink(missing_ok=True)
        journal.remover_staging(staging)
    pendentes = journal.listar_manifestos(raiz, journal.PENDING, limits)
    for _, manifesto in pendentes:
        journal.limpar_operacao(raiz, str(manifesto["operation_id"]), limits)
    descartados = len(pendentes) + journal.limpar_orfos(
        raiz, confirmados, pendentes, limits
    )
    if operacoes or descartados:
        _registar(
            audit,
            context,
            "workspace.recovery",
            "Recuperação do workspace concluída.",
            {"operation_id": operacoes[0] if operacoes else "0" * 32, "count": descartados},
        )
    return RecoveryReport(tuple(operacoes), restaurados, descartados)


def _registar_commit(raiz: Path, operacao: str, limits: FileOpLimits) -> None:
    """Marca a operação como confirmada com uma única substituição atómica."""
    origem = journal.caminho_interno(
        raiz, f"{journal.DIRETORIO}/{journal.PENDING}/{operacao}.json", limits
    )
    destino = journal.caminho_interno(
        raiz, f"{journal.DIRETORIO}/{journal.COMMITTED}/{operacao}.json", limits
    )
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        os.replace(origem, destino)
    except OSError as exc:
        raise FileOpsError("O commit da operação não pôde ser gravado.") from exc


def _aplicar_manifest(
    caminhos: tuple[Path, Path],
    manifesto: Mapping[str, object],
    context: EventContext,
    audit: AuditTrail,
    limits: FileOpLimits,
) -> int:
    """Aplica cada ficheiro confirmado e verifica o digest final."""
    raiz, staging = caminhos
    operacao = str(manifesto["operation_id"])
    gravados = 0
    ficheiros = cast("Sequence[Mapping[str, object]]", manifesto["files"])
    entradas = tuple(journal.entrada(item) for item in ficheiros)
    for item in entradas:
        relativo = str(item["path"])
        origem = validate_workspace_path(staging, relativo, max_chars=limits.max_chars)
        destino = validate_workspace_path(raiz, relativo, max_chars=limits.max_chars)
        digest, tamanho = journal.digest_arquivo(origem, limits.max_file_bytes)
        if digest != item["sha256"] or tamanho != item["size"]:
            raise FileOpsError("Um ficheiro preparado falhou a verificação de hash.")
        if _igual(destino, item):
            continue
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            _substituir(origem, destino)
        except OSError as exc:
            raise FileOpsError("A substituição atómica falhou.") from exc
        _registar(
            audit,
            context,
            "workspace.write",
            "Ficheiro gravado de forma atómica.",
            {
                "operation_id": operacao,
                "path": relativo,
                "sha256": digest,
                "size": tamanho,
            },
        )
        gravados += 1
    if not _igual_manifest(raiz, entradas, limits):
        raise FileOpsError("O estado final não corresponde ao commit confirmado.")
    return gravados


def _substituir(origem: Path, destino: Path) -> None:
    """Substitui um ficheiro por outro dentro da mesma raiz."""
    os.replace(origem, destino)


def _validar_alteracoes(
    raiz: Path, changes: Iterable[FileChange], limits: FileOpLimits
) -> tuple[dict[str, object], ...]:
    """Valida todas as alterações antes de qualquer escrita."""
    previstos: list[dict[str, object]] = []
    vistos: set[str] = set()
    total = 0
    for alteracao in changes:
        if not isinstance(alteracao, FileChange):
            raise FileOpsError("Cada alteração tem de ser um FileChange.")
        try:
            destino = validate_workspace_path(
                raiz, alteracao.path, max_chars=limits.max_chars
            )
        except WorkspacePathError as exc:
            raise FileOpsError("O caminho da escrita não é seguro.") from exc
        relativo = destino.relative_to(raiz).as_posix()
        if journal.eh_interno(relativo):
            raise FileOpsError("Não é permitido escrever em pastas internas.")
        if relativo in vistos:
            raise FileOpsError("O mesmo caminho foi indicado mais de uma vez.")
        if not isinstance(alteracao.data, bytes):
            raise FileOpsError("O conteúdo da escrita tem de ser bytes.")
        if len(alteracao.data) > limits.max_file_bytes:
            raise FileOpsError("O ficheiro excede o limite de bytes por escrita.")
        total += len(alteracao.data)
        if total > limits.max_total_bytes:
            raise FileOpsError("A operação excede o total de bytes permitido.")
        vistos.add(relativo)
        previstos.append({
            "path": relativo,
            "size": len(alteracao.data),
            "sha256": hashlib.sha256(alteracao.data).hexdigest(),
            "data": alteracao.data,
        })
    if not previstos or len(previstos) > limits.max_files:
        raise FileOpsError("A operação tem um número inválido de ficheiros.")
    return tuple(previstos)


def _gravar_staging(
    staging: Path, previstos: Sequence[Mapping[str, object]], limits: FileOpLimits
) -> None:
    """Copia os conteúdos validados para o staging e confirma os hashes."""
    for item in previstos:
        relativo = str(item["path"])
        destino = validate_workspace_path(staging, relativo, max_chars=limits.max_chars)
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            with destino.open("xb") as ficheiro:
                ficheiro.write(cast(bytes, item["data"]))
        except OSError as exc:
            raise FileOpsError("O conteúdo não pôde ser preparado.") from exc
        digest, tamanho = journal.digest_arquivo(destino, limits.max_file_bytes)
        if digest != item["sha256"] or tamanho != item["size"]:
            raise FileOpsError("O conteúdo preparado mudou durante a cópia.")


def _igual(destino: Path, entrada: Mapping[str, object]) -> bool:
    """Indica se o ficheiro final já tem o tamanho e o hash esperados."""
    try:
        digest, tamanho = journal.digest_arquivo(destino, int(str(entrada["size"])))
    except FileOpsError:
        return False
    return digest == entrada["sha256"] and tamanho == entrada["size"]


def _igual_manifest(
    raiz: Path, entradas: Sequence[Mapping[str, object]], limits: FileOpLimits
) -> bool:
    """Confirma todos os ficheiros declarados no manifesto."""
    for entrada in entradas:
        destino = validate_workspace_path(
            raiz, str(entrada["path"]), max_chars=limits.max_chars
        )
        if not _igual(destino, entrada):
            return False
    return True


def _registar(
    audit: AuditTrail,
    context: EventContext,
    kind: str,
    message: str,
    data: Mapping[str, object],
) -> None:
    """Regista um evento de auditoria com os metadados da operação."""
    nivel = {
        "workspace.failed": EventLevel.ERROR,
        "workspace.interrupted": EventLevel.WARNING,
    }.get(kind, EventLevel.INFO)
    try:
        audit.record(context, kind=kind, message=message, data=data, level=nivel)
    except AuditError as exc:
        raise FileOpsError("O evento de auditoria não pôde ser gravado.") from exc
