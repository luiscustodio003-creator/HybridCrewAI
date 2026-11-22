"""Recuperação real após morte súbita do processo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from app.core.tasks import TaskStatus, transitar
from app.core.tasks.store_sqlite import SqliteTaskStore

RAIZ = Path(__file__).resolve().parents[2]
CHAVE = "recovery:kill-resume"
LIMITE_LEITURA = 20

TRABALHADOR = """
import sys
import time

sys.path.insert(0, sys.argv[1])

from app.core.tasks import TaskSpec, TaskStatus, new_task, transitar
from app.core.tasks.store_sqlite import SqliteTaskStore

loja = SqliteTaskStore(sys.argv[2])
loja.initialize()
tarefa = new_task(
    TaskSpec(
        title="Tarefa interrompida",
        description="Teste de recuperacao real",
        agent="open-code",
        phase="1",
        chave=sys.argv[3],
    )
)
loja.save(tarefa)
loja.save(transitar(tarefa, TaskStatus.QUEUED))
loja.save(transitar(loja.get(tarefa.task_id), TaskStatus.RUNNING))
print("PRONTO:" + tarefa.task_id, flush=True)
time.sleep(60)
"""


def test_kill_resume_com_sqlite_real(tmp_path: Path) -> None:
    """Um processo morto deixa uma tarefa recuperável e retomável."""
    caminho = tmp_path / "tarefas.db"
    processo = subprocess.Popen(
        [
            sys.executable,
            "-c",
            TRABALHADOR,
            str(RAIZ),
            str(caminho),
            CHAVE,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    fila: Queue[str | None] = Queue()
    Thread(
        target=lambda: fila.put(processo.stdout.readline() if processo.stdout else None),
        daemon=True,
    ).start()
    try:
        linha = fila.get(timeout=LIMITE_LEITURA)
    except Empty:
        processo.kill()
        processo.communicate(timeout=10)
        raise AssertionError("O processo de recuperação não sinalizou PRONTO.") from None
    assert linha, "O processo terminou sem sinalizar PRONTO."
    assert linha.startswith("PRONTO:")
    task_id = linha.split(":", 1)[1].strip()
    processo.kill()
    processo.communicate(timeout=10)

    assert caminho.exists(), "O ficheiro SQLite não foi criado pelo subprocesso."
    loja = SqliteTaskStore(caminho)
    loja.initialize()
    antes = loja.get(task_id)
    assert antes is not None
    assert antes.status is TaskStatus.RUNNING

    recuperadas = loja.recover_orphans()
    assert [tarefa.task_id for tarefa in recuperadas] == [task_id]
    interrompida = loja.get(task_id)
    assert interrompida is not None
    assert interrompida.status is TaskStatus.INTERRUPTED

    retomada = transitar(interrompida, TaskStatus.QUEUED)
    assert transitar(retomada, TaskStatus.RUNNING).status is TaskStatus.RUNNING
