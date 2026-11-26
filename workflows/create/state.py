"""Persistência de checkpoints e chaves de idempotência do fluxo CREATE."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from workflows.create.models import (
    PASSOS,
    Checkpoint,
    Step,
    WorkflowError,
)

from app.core.tasks import TaskStatus, utc_now


class CheckpointStoreError(WorkflowError):
    """Falha ao gravar ou ler um checkpoint."""


class CheckpointStore:
    """Armazém SQLite de checkpoints e passos já confirmados."""

    __slots__ = ("_ligacao",)

    def __init__(self, path: str | Path) -> None:
        """Abre a base local e cria as tabelas necessárias."""
        self._ligacao = sqlite3.connect(str(path), timeout=5)
        self._ligacao.row_factory = sqlite3.Row
        self._criar_tabelas()

    def _criar_tabelas(self) -> None:
        """Cria as tabelas de estado e de idempotência."""
        with self._ligacao:
            self._ligacao.execute(
                """
                CREATE TABLE IF NOT EXISTS create_checkpoints (
                    task_id TEXT PRIMARY KEY,
                    correlation_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_completed_step TEXT,
                    pending_token_hash TEXT,
                    agent TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ligacao.execute(
                """
                CREATE TABLE IF NOT EXISTS create_idempotency (
                    task_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (task_id, step)
                )
                """
            )

    def save(self, checkpoint: Checkpoint) -> None:
        """Grava ou actualiza um checkpoint de forma atómica."""
        if not isinstance(checkpoint, Checkpoint):
            raise CheckpointStoreError("checkpoint tem de ser Checkpoint.")
        with self._ligacao:
            self._ligacao.execute(
                """
                INSERT INTO create_checkpoints (
                    task_id, correlation_id, status, last_completed_step,
                    pending_token_hash, agent, phase, version, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    correlation_id = excluded.correlation_id,
                    status = excluded.status,
                    last_completed_step = excluded.last_completed_step,
                    pending_token_hash = excluded.pending_token_hash,
                    agent = excluded.agent,
                    phase = excluded.phase,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    checkpoint.task_id,
                    checkpoint.correlation_id,
                    checkpoint.status.value,
                    (
                        checkpoint.last_completed_step.value
                        if checkpoint.last_completed_step
                        else None
                    ),
                    checkpoint.pending_token_hash,
                    checkpoint.agent,
                    checkpoint.phase,
                    checkpoint.version,
                    checkpoint.updated_at.isoformat(),
                ),
            )

    def get(self, task_id: str) -> Checkpoint | None:
        """Devolve o checkpoint de uma tarefa ou None quando não existe."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise CheckpointStoreError("task_id tem de ser texto não vazio.")
        linha = self._ligacao.execute(
            "SELECT * FROM create_checkpoints WHERE task_id = ?", (task_id.strip(),)
        ).fetchone()
        if linha is None:
            return None
        return self._converter(linha)

    def cancelar(self, task_id: str) -> Checkpoint | None:
        """Marca um checkpoint como CANCELLED sem apagar os passos confirmados."""
        checkpoint = self.get(task_id)
        if checkpoint is None or checkpoint.status is TaskStatus.CANCELLED:
            return checkpoint
        cancelado = replace(
            checkpoint,
            status=TaskStatus.CANCELLED,
            version=checkpoint.version + 1,
            updated_at=utc_now(),
        )
        self.save(cancelado)
        return cancelado

    def recover_interrupted(
        self, task_ids: Sequence[str] | None = None
    ) -> list[Checkpoint]:
        """Marca como INTERRUPTED os checkpoints RUNNING das tarefas indicadas."""
        alvos: set[str] | None = None
        if task_ids is not None:
            alvos = set()
            for identificador in task_ids:
                if not isinstance(identificador, str) or not identificador.strip():
                    raise CheckpointStoreError(
                        "task_ids tem de conter identificadores não vazios."
                    )
                alvos.add(identificador.strip())
        linhas = self._ligacao.execute(
            "SELECT task_id FROM create_checkpoints WHERE status = ?",
            (TaskStatus.RUNNING.value,),
        ).fetchall()
        recuperados: list[Checkpoint] = []
        for linha in linhas:
            identificador = linha["task_id"]
            if alvos is not None and identificador not in alvos:
                continue
            checkpoint = self.get(identificador)
            if checkpoint is None:
                continue
            interrompido = replace(
                checkpoint,
                status=TaskStatus.INTERRUPTED,
                version=checkpoint.version + 1,
                updated_at=utc_now(),
            )
            self.save(interrompido)
            recuperados.append(interrompido)
        return recuperados

    def _garantir_ativo(self, task_id: str) -> None:
        """Impede a execução de passos num fluxo cancelado."""
        checkpoint = self.get(task_id)
        if checkpoint is not None and checkpoint.status is TaskStatus.CANCELLED:
            raise CheckpointStoreError(
                "Fluxo cancelado; não é possível executar novos passos."
            )

    def _validar_chave(self, task_id: str, passo: Step, chave: str) -> None:
        """Valida os argumentos de uma chave de idempotência."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise CheckpointStoreError("task_id tem de ser texto não vazio.")
        if passo not in PASSOS:
            raise CheckpointStoreError("passo desconhecido.")
        if not isinstance(chave, str) or not chave.strip():
            raise CheckpointStoreError("chave tem de ser texto não vazio.")

    def ja_registrada(self, task_id: str, passo: Step, chave: str) -> bool:
        """Indica se uma chave de idempotência já foi confirmada."""
        self._validar_chave(task_id, passo, chave)
        self._garantir_ativo(task_id)
        linha = self._ligacao.execute(
            """
            SELECT 1 FROM create_idempotency
            WHERE task_id = ? AND step = ? AND chave = ?
            """,
            (task_id.strip(), passo.value, chave.strip()),
        ).fetchone()
        return linha is not None

    def registrar_chave(self, task_id: str, passo: Step, chave: str) -> bool:
        """Regista uma chave de idempotência e indica se o passo é novo."""
        self._validar_chave(task_id, passo, chave)
        self._garantir_ativo(task_id)
        with self._ligacao:
            cursor = self._ligacao.execute(
                """
                INSERT OR IGNORE INTO create_idempotency (
                    task_id, step, chave, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (task_id.strip(), passo.value, chave.strip(), utc_now().isoformat()),
            )
        return cursor.rowcount == 1

    def _converter(self, linha: sqlite3.Row) -> Checkpoint:
        """Converte uma linha SQLite num checkpoint validado."""
        try:
            passo = (
                Step(linha["last_completed_step"])
                if linha["last_completed_step"] is not None
                else None
            )
            return Checkpoint(
                task_id=linha["task_id"],
                correlation_id=linha["correlation_id"],
                status=TaskStatus(linha["status"]),
                last_completed_step=passo,
                pending_token_hash=linha["pending_token_hash"],
                agent=linha["agent"],
                phase=linha["phase"],
                version=linha["version"],
                updated_at=datetime.fromisoformat(linha["updated_at"]),
            )
        except (TypeError, ValueError) as erro:
            raise CheckpointStoreError("Checkpoint gravado é inválido.") from erro
