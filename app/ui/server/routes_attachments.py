"""Rotas de anexos em quarentena e do relatório de cobertura."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from approvals.tokens import ApprovalDenied, TokenStore

from app.core.config import Settings
from app.core.tasks import utc_now
from app.llm.egress import redact_text
from app.ui.server.attachments_contract import (
    ATTACHMENTS_PATH,
    ERROS,
    RELEASE_PATH,
    analisar_release,
    analisar_upload,
    ler_corpo,
    validar_aprovacao,
)
from app.ui.server.attachments_contract import (
    limite_corpo as _limite_corpo,
)
from app.ui.server.attachments_paths import (
    gravar_staging,
    limites_extracao,
    limites_quarentena,
    raiz,
    validar_zip,
)
from app.ui.server.chat import ChatMessage, ChatService
from app.workspace import (
    WorkspaceScan,
    ingest_zip,
    quarantine_attachment,
    release_quarantine,
    scan_workspace,
)


def limite_corpo(caminho: str, settings: Settings) -> int:
    """Devolve o limite do corpo para a rota de anexos pedida."""
    return _limite_corpo(caminho, settings.max_zip_bytes)


def caminhos_post(settings: Settings) -> frozenset[str]:
    """Devolve as rotas POST activas conforme as funcionalidades."""
    caminhos: set[str] = set()
    if settings.attachments and settings.zip_enabled:
        caminhos.add(ATTACHMENTS_PATH)
    if settings.attachments and settings.workspace_write:
        caminhos.add(RELEASE_PATH)
    return frozenset(caminhos)


def resposta_anexo(
    handler: BaseHTTPRequestHandler,
    settings: Settings,
    tokens: TokenStore,
    chat_service: ChatService,
    caminho: str,
) -> tuple[HTTPStatus, dict[str, object]]:
    """Processa um anexo e devolve o estado HTTP e o corpo JSON."""
    try:
        corpo = ler_corpo(handler, limite_corpo(caminho, settings))
        if caminho == ATTACHMENTS_PATH:
            return HTTPStatus.OK, _upload(corpo, settings, tokens, chat_service)
        return HTTPStatus.OK, _libertar(corpo, settings, tokens, chat_service)
    except ApprovalDenied as exc:
        return _resposta_erro(HTTPStatus.FORBIDDEN, exc)
    except ERROS as exc:
        return _resposta_erro(HTTPStatus.BAD_REQUEST, exc)


def _resposta_erro(
    status: HTTPStatus, erro: Exception
) -> tuple[HTTPStatus, dict[str, object]]:
    """Converte um erro em resposta JSON sem revelar dados sensíveis."""
    return status, {"error": {"message": redact_text(str(erro))}}


def _upload(
    corpo: bytes, settings: Settings, tokens: TokenStore, chat: ChatService
) -> dict[str, object]:
    """Retém um ZIP validado em quarentena até aprovação explícita."""
    pedido = analisar_upload(corpo)
    validar_aprovacao(tokens, pedido)
    caminho = raiz(settings)
    validar_zip(pedido.dados, caminho, settings)
    temporario = gravar_staging(caminho, settings, pedido.filename, pedido.dados)
    try:
        registro = quarantine_attachment(
            caminho,
            temporario,
            relative_name=temporario.relative_to(caminho).as_posix(),
            approval_token=pedido.approval_token,
            limits=limites_quarentena(settings),
        )
    finally:
        shutil.rmtree(temporario.parent, ignore_errors=True)
    mensagem = (
        f"Anexo {pedido.filename} em quarentena: {registro.sha256}. "
        "Aguarda aprovação para leitura."
    )
    _guardar_mensagem(chat, mensagem, pedido.task_id, pedido.correlation_id)
    return {
        "state": "quarantined",
        "attachment_id": registro.id,
        "filename": pedido.filename,
        "sha256": registro.sha256,
        "size": registro.size,
    }


def _libertar(
    corpo: bytes, settings: Settings, tokens: TokenStore, chat: ChatService
) -> dict[str, object]:
    """Liberta um anexo aprovado e devolve a cobertura real do disco."""
    pedido = analisar_release(corpo)
    validar_aprovacao(tokens, pedido)
    caminho = raiz(settings)
    destino = f"anexos/{pedido.attachment_id}"
    caminho_zip = release_quarantine(
        caminho,
        pedido.attachment_id,
        approval_token=pedido.approval_token,
        limits=limites_quarentena(settings),
    )
    try:
        ingest_zip(
            caminho,
            caminho_zip,
            destination=destino,
            limits=limites_extracao(settings),
        )
    finally:
        shutil.rmtree(caminho_zip.parent, ignore_errors=True)
    varredura = scan_workspace(
        caminho / destino,
        max_chars=settings.max_workspace_path_chars,
        max_file_bytes=settings.max_workspace_file_bytes,
    )
    relatorio = _relatorio(destino, varredura)
    mensagem = _mensagem_cobertura(relatorio)
    _guardar_mensagem(chat, mensagem, pedido.task_id, pedido.correlation_id)
    return {
        "state": "released",
        "attachment_id": pedido.attachment_id,
        "report": relatorio,
    }


def _relatorio(destino: str, varredura: WorkspaceScan) -> dict[str, object]:
    """Converte a varredura num relatório com caminhos prefixados."""
    return {
        "destination": destino,
        "lidos": [
            {"path": f"{destino}/{caminho}"} for caminho in varredura.readable
        ],
        "ignorados": [
            {"path": f"{destino}/{item.path}", "reason": item.reason.value}
            for item in varredura.ignored
        ],
        "total_on_disk": varredura.total_on_disk,
        "total_classified": varredura.total_classified,
        "coverage_complete": varredura.coverage_complete,
    }


def _mensagem_cobertura(relatorio: Mapping[str, object]) -> str:
    """Resume a cobertura sem copiar conteúdos dos ficheiros."""
    linhas = ["Cobertura do anexo libertado:"]
    lidos = relatorio["lidos"]
    ignorados = relatorio["ignorados"]
    assert isinstance(lidos, list) and isinstance(ignorados, list)
    linhas.append(
        f"lidos: {len(lidos)}; ignorados: {len(ignorados)}; "
        f"total no disco: {relatorio['total_on_disk']}."
    )
    for item in lidos:
        assert isinstance(item, dict)
        linhas.append(f"lido: {item['path']}")
    for item in ignorados:
        assert isinstance(item, dict)
        linhas.append(f"ignorado: {item['path']} ({item['reason']})")
    return "\n".join(linhas)


def _guardar_mensagem(
    chat: ChatService, conteudo: str, tarefa: str, correlacao: str
) -> None:
    """Persiste um aviso do anexo com redacção de segredos."""
    chat.store.save(
        ChatMessage(
            "assistant",
            redact_text(conteudo),
            tarefa,
            correlacao,
            utc_now(),
        )
    )


__all__ = [
    "ATTACHMENTS_PATH",
    "RELEASE_PATH",
    "caminhos_post",
    "limite_corpo",
    "resposta_anexo",
]
