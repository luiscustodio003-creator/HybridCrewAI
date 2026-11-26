"""Executor simples não isolado com aprovação prévia e subprocesso vigiado."""

from __future__ import annotations

import hashlib
import hmac
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from approvals.tokens import ApprovalDenied, ApprovalError, TokenStore

from app.core.events import EventBus, EventContext, EventLevel, new_event
from app.core.results import ToolStatus, new_tool_result
from execution.guard import GUARDA_SUBPROCESSO, ambiente_limpo
from execution.models import ExecutionRequest, ExecutionResult

if TYPE_CHECKING:
    from approvals.tokens import ApprovalToken

    from app.core.config import Settings

AGENTE = "simple-runner"
FASE = "4"
INTERVALO_SONDA_S = 0.05
CONCLUIDO, TEMPO, CANCELADO = "concluido", "tempo", "cancelado"


class SimpleRunner:
    """Executa comandos aprovados numa pasta temporária dentro do workspace."""

    def __init__(
        self,
        settings: Settings,
        tokens: TokenStore,
        events: EventBus | None = None,
    ) -> None:
        """Configura dependências explícitas sem recursos globais."""
        self._settings = settings
        self._tokens = tokens
        self._events = events

    def executar(self, pedido: ExecutionRequest) -> ExecutionResult:
        """Valida a aprovação e executa o comando com prazo e cancelamento."""
        contexto = _contexto(pedido)
        try:
            self._autorizar(pedido)
        except ApprovalError as exc:
            return self._recusar(contexto, exc)
        return self._executar_processo(contexto, pedido)

    def _autorizar(self, pedido: ExecutionRequest) -> ApprovalToken:
        """Confere token, tarefa, diff, prazo e correlação antes da execução."""
        token = self._tokens.validar(
            pedido.approval_token, pedido.task_id, pedido.diff_hash
        )
        if not hmac.compare_digest(token.correlation_id, pedido.correlation_id):
            raise ApprovalDenied("A correlação do token não corresponde à pedida.")
        return token

    def _recusar(self, contexto: EventContext, exc: ApprovalError) -> ExecutionResult:
        """Devolve falha verificável quando a aprovação não é aceite."""
        mensagem = f"aprovação recusada: {exc}"
        self._publicar(
            contexto,
            "execution.recusado",
            "Execução recusada antes de iniciar subprocesso.",
            EventLevel.WARNING,
            {"isolated": False, "motivo": type(exc).__name__},
        )
        return ExecutionResult(
            tool_result=new_tool_result(
                ToolStatus.FAILED, "Execução recusada.", error=mensagem
            ),
            isolated=False,
        )

    def _executar_processo(
        self, contexto: EventContext, pedido: ExecutionRequest
    ) -> ExecutionResult:
        """Cria a pasta temporária, lança o processo e aplica limites."""
        self._settings.data_dir.mkdir(parents=True, exist_ok=True)
        inicio = time.monotonic()
        with tempfile.TemporaryDirectory(
            prefix="exec-", dir=self._settings.data_dir
        ) as nome:
            destino = Path(nome)
            (destino / "sitecustomize.py").write_text(
                GUARDA_SUBPROCESSO, encoding="utf-8"
            )
            self._publicar(
                contexto,
                "execution.iniciado",
                "Subprocesso iniciado em pasta temporária.",
                data={"isolated": False, "workspace": destino.name},
            )
            try:
                processo = subprocess.Popen(
                    pedido.command,
                    cwd=destino,
                    env=ambiente_limpo(destino),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except OSError as exc:
                return self._falha_inicio(
                    contexto,
                    f"Falha ao iniciar processo: {exc}",
                    destino,
                    inicio,
                )
            captura = self._aguardar(processo, pedido, inicio)
            if captura[2] != CONCLUIDO:
                _terminar(processo)
                captura = _colectar(processo, captura)
            return self._concluir(contexto, processo, destino, inicio, captura)

    def _aguardar(
        self,
        processo: subprocess.Popen[str],
        pedido: ExecutionRequest,
        inicio: float,
    ) -> tuple[str, str, str]:
        """Sonda o processo até terminar, expirar ou receber cancelamento."""
        while True:
            try:
                saida, erro = processo.communicate(timeout=INTERVALO_SONDA_S)
                return saida or "", erro or "", CONCLUIDO
            except subprocess.TimeoutExpired:
                if pedido.cancel_event is not None and pedido.cancel_event.is_set():
                    return "", "", CANCELADO
                if time.monotonic() - inicio >= pedido.timeout_s:
                    return "", "", TEMPO

    def _concluir(
        self,
        contexto: EventContext,
        processo: subprocess.Popen[str],
        destino: Path,
        inicio: float,
        captura: tuple[str, str, str],
    ) -> ExecutionResult:
        """Constrói o resultado e publica o evento final correspondente."""
        saida, erro, motivo = captura
        duracao_ms = round((time.monotonic() - inicio) * 1000, 1)
        dados = _dados_processo(destino, duracao_ms, saida, erro)
        if motivo == TEMPO:
            return self._falha_evento(
                contexto, "Tempo limite excedido.", dados, processo.returncode
            )
        if motivo == CANCELADO:
            return self._falha_evento(
                contexto, "Execução cancelada.", dados, processo.returncode
            )
        if processo.returncode != 0:
            return self._falha_evento(
                contexto,
                f"Processo terminou com código {processo.returncode}.",
                dados,
                processo.returncode,
            )
        evidencia = (
            f"workspace={destino.name}",
            f"returncode={processo.returncode}",
            f"stdout_sha256={hashlib.sha256(saida.encode('utf-8')).hexdigest()}",
        )
        self._publicar(
            contexto,
            "execution.concluido",
            "Subprocesso concluído com sucesso.",
            data={**dados, "returncode": processo.returncode, "isolated": False},
        )
        return ExecutionResult(
            tool_result=new_tool_result(
                ToolStatus.DONE, "Subprocesso concluído.", evidence=evidencia
            ),
            isolated=False,
            returncode=processo.returncode,
            workspace=str(destino),
            stdout=saida,
            stderr=erro,
            duration_ms=duracao_ms,
        )

    def _falha_inicio(
        self,
        contexto: EventContext,
        mensagem: str,
        destino: Path,
        inicio: float,
    ) -> ExecutionResult:
        """Publica e devolve falha quando o processo nem chegou a arrancar."""
        self._publicar(
            contexto,
            "execution.falhado",
            mensagem,
            EventLevel.WARNING,
            {"isolated": False, "workspace": destino.name},
        )
        return ExecutionResult(
            tool_result=new_tool_result(
                ToolStatus.FAILED, "Execução não iniciada.", error=mensagem
            ),
            isolated=False,
            workspace=str(destino),
            duration_ms=round((time.monotonic() - inicio) * 1000, 1),
        )

    def _falha_evento(
        self,
        contexto: EventContext,
        mensagem: str,
        dados: dict[str, object],
        returncode: int | None,
    ) -> ExecutionResult:
        """Publica falha e devolve o resultado com isolamento explícito."""
        self._publicar(
            contexto,
            "execution.falhado",
            mensagem,
            EventLevel.WARNING,
            {**dados, "returncode": returncode, "isolated": False},
        )
        return ExecutionResult(
            tool_result=new_tool_result(
                ToolStatus.FAILED, "Subprocesso não concluído.", error=mensagem
            ),
            isolated=False,
            returncode=returncode,
            workspace=str(dados["workspace"]),
            stdout=str(dados["stdout"]),
            stderr=str(dados["stderr"]),
            duration_ms=float(str(dados["duration_ms"])),
        )

    def _publicar(
        self,
        contexto: EventContext,
        kind: str,
        mensagem: str,
        level: EventLevel = EventLevel.INFO,
        data: dict[str, object] | None = None,
    ) -> None:
        """Publica eventos quando existe barramento configurado."""
        if self._events is not None:
            self._events.publish(
                new_event(contexto, kind=kind, message=mensagem, level=level, data=data)
            )


def _contexto(pedido: ExecutionRequest) -> EventContext:
    """Constrói o contexto obrigatório de rastreabilidade do executor."""
    return EventContext(
        correlation_id=pedido.correlation_id,
        task_id=pedido.task_id,
        agent=AGENTE,
        phase=FASE,
    )


def _terminar(processo: subprocess.Popen[str]) -> None:
    """Termina o processo e aplica killing apenas como último recurso."""
    if processo.poll() is not None:
        return
    processo.terminate()
    try:
        processo.wait(timeout=2)
    except subprocess.TimeoutExpired:
        processo.kill()
        processo.wait(timeout=2)


def _colectar(
    processo: subprocess.Popen[str], captura: tuple[str, str, str]
) -> tuple[str, str, str]:
    """Recolhe a saída pendente depois de terminar ou cancelar."""
    saida, erro, motivo = captura
    try:
        nova_saida, novo_erro = processo.communicate(timeout=2)
        return nova_saida or saida, novo_erro or erro, motivo
    except subprocess.TimeoutExpired:
        return saida, erro, motivo


def _dados_processo(
    destino: Path, duracao_ms: float, saida: str, erro: str
) -> dict[str, object]:
    """Projeta metadados seguros do processo para eventos e resultados."""
    return {
        "workspace": str(destino),
        "duration_ms": duracao_ms,
        "stdout": saida[:2000],
        "stderr": erro[:2000],
    }
