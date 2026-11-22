"""Persistência SQLite de tarefas e recuperação de órfãs."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.core.tasks.model import Task
from app.core.tasks.state_machine import TaskStatus, transitar

_SQL_CRIAR = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    agent TEXT NOT NULL,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    attempts INTEGER NOT NULL
)
"""
_SQL_GUARDAR = """
INSERT INTO tasks (
    task_id, title, description, agent, phase, status,
    created_at, updated_at, attempts
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(task_id) DO UPDATE SET
    title=excluded.title,
    description=excluded.description,
    agent=excluded.agent,
    phase=excluded.phase,
    status=excluded.status,
    created_at=excluded.created_at,
    updated_at=excluded.updated_at,
    attempts=excluded.attempts
"""


class SqliteTaskStore:
    """Armazena tarefas num ficheiro SQLite real."""

    __slots__ = ("_path",)

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Caminho do ficheiro de base de dados."""
        return self._path

    def _connect(self) -> sqlite3.Connection:
        """Abre uma ligação com espera por bloqueios."""
        ligacao = sqlite3.connect(self._path, timeout=5)
        ligacao.row_factory = sqlite3.Row
        ligacao.execute("PRAGMA busy_timeout=5000")
        return ligacao

    def initialize(self) -> None:
        """Cria a pasta e a tabela de tarefas, se necessário."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as ligacao:
            with ligacao:
                ligacao.execute(_SQL_CRIAR)

    @staticmethod
    def _linha(tarefa: Task) -> tuple[object, ...]:
        """Converte uma tarefa nos valores da linha SQLite."""
        return (
            tarefa.task_id,
            tarefa.title,
            tarefa.description,
            tarefa.agent,
            tarefa.phase,
            tarefa.status.value,
            tarefa.created_at.isoformat(),
            tarefa.updated_at.isoformat(),
            tarefa.attempts,
        )

    @staticmethod
    def _tarefa(linha: sqlite3.Row) -> Task:
        """Reconstrói uma tarefa a partir de uma linha SQLite."""
        return Task(
            task_id=linha["task_id"],
            title=linha["title"],
            description=linha["description"],
            agent=linha["agent"],
            phase=linha["phase"],
            status=TaskStatus(linha["status"]),
            created_at=datetime.fromisoformat(linha["created_at"]),
            updated_at=datetime.fromisoformat(linha["updated_at"]),
            attempts=linha["attempts"],
        )

    @staticmethod
    def _guardar(ligacao: sqlite3.Connection, tarefa: Task) -> None:
        """Grava ou actualiza uma tarefa usando a ligação indicada."""
        ligacao.execute(_SQL_GUARDAR, SqliteTaskStore._linha(tarefa))

    def save(self, tarefa: Task) -> None:
        """Grava ou actualiza uma tarefa."""
        with closing(self._connect()) as ligacao:
            with ligacao:
                self._guardar(ligacao, tarefa)

    def get(self, task_id: str) -> Task | None:
        """Devolve uma tarefa pelo identificador ou None."""
        with closing(self._connect()) as ligacao:
            linha = ligacao.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
        return None if linha is None else self._tarefa(linha)

    def list_tasks(self) -> list[Task]:
        """Devolve todas as tarefas gravadas."""
        with closing(self._connect()) as ligacao:
            linhas = ligacao.execute("SELECT * FROM tasks ORDER BY created_at").fetchall()
        return [self._tarefa(linha) for linha in linhas]

    def recover_orphans(self) -> list[Task]:
        """Marca tarefas RUNNING de processos mortos como INTERRUPTED."""
        recuperadas: list[Task] = []
        with closing(self._connect()) as ligacao:
            linhas = ligacao.execute(
                "SELECT * FROM tasks WHERE status = ?", (TaskStatus.RUNNING.value,)
            ).fetchall()
            for linha in linhas:
                interrompida = transitar(self._tarefa(linha), TaskStatus.INTERRUPTED)
                with ligacao:
                    self._guardar(ligacao, interrompida)
                recuperadas.append(interrompida)
        return recuperadas
