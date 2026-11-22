"""Testes do modelo e da máquina de estados de tarefas."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.tasks import (
    Task,
    TaskSpec,
    TaskStateError,
    TaskStatus,
    generate_task_id,
    new_task,
    pode_transitar,
    transitar,
)

CHAVE = "HCW-01-006:modelo"
TAMANHO_UUID = 36


def criar_tarefa(status: TaskStatus = TaskStatus.CREATED) -> Task:
    """Cria uma tarefa válida para os testes."""
    return new_task(
        TaskSpec(
            title="Modelo de tarefas",
            description="Validar estados",
            agent="open-code",
            phase="1",
            chave=CHAVE,
            status=status,
        )
    )


def test_ids_unicos_e_estaveis_entre_reinicios() -> None:
    primeiro = generate_task_id(CHAVE)
    segundo = generate_task_id(CHAVE)
    outro = generate_task_id("HCW-01-006:outro")
    assert primeiro == segundo
    assert primeiro != outro
    assert len(primeiro) == TAMANHO_UUID


def test_transicao_invalida_completed_para_running_e_rejeitada() -> None:
    tarefa = criar_tarefa(TaskStatus.COMPLETED)
    with pytest.raises(TaskStateError, match="COMPLETED.*RUNNING"):
        transitar(tarefa, TaskStatus.RUNNING)


def test_running_pode_ser_interrompida() -> None:
    tarefa = criar_tarefa(TaskStatus.RUNNING)
    assert pode_transitar(TaskStatus.RUNNING, TaskStatus.INTERRUPTED)
    interrompida = transitar(tarefa, TaskStatus.INTERRUPTED)
    assert interrompida.status is TaskStatus.INTERRUPTED


def test_interrompida_pode_reenfileirar_para_recuperacao() -> None:
    interrompida = criar_tarefa(TaskStatus.INTERRUPTED)
    assert pode_transitar(TaskStatus.INTERRUPTED, TaskStatus.QUEUED)
    assert transitar(interrompida, TaskStatus.QUEUED).status is TaskStatus.QUEUED


def test_fluxo_valido_de_criacao_a_conclusao() -> None:
    tarefa = criar_tarefa()
    estados = [
        TaskStatus.QUEUED,
        TaskStatus.RUNNING,
        TaskStatus.COMPLETED,
    ]
    for estado in estados:
        tarefa = transitar(tarefa, estado)
    assert tarefa.status is TaskStatus.COMPLETED
    assert tarefa.attempts == 1


def test_estado_terminal_nao_aceita_transicao() -> None:
    tarefa = criar_tarefa(TaskStatus.FAILED)
    with pytest.raises(TaskStateError):
        transitar(tarefa, TaskStatus.RUNNING)


def test_campos_obrigatorios_sao_validados() -> None:
    with pytest.raises(ValueError, match="title"):
        new_task(
            TaskSpec(
                title="  ",
                description="x",
                agent="a",
                phase="1",
                chave=CHAVE,
            )
        )


def test_tarefa_e_imutavel() -> None:
    tarefa = criar_tarefa()
    with pytest.raises((AttributeError, ValueError)):
        tarefa.status = TaskStatus.RUNNING  # type: ignore[misc]


def test_timestamp_e_utc_e_mudado_na_transicao() -> None:
    antiga = criar_tarefa()
    antiga = Task(
        task_id=antiga.task_id,
        title=antiga.title,
        description=antiga.description,
        agent=antiga.agent,
        phase=antiga.phase,
        status=antiga.status,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
        updated_at=datetime(2020, 1, 1, tzinfo=UTC),
        attempts=0,
    )
    nova = transitar(antiga, TaskStatus.QUEUED)
    assert nova.updated_at > antiga.updated_at
    assert nova.created_at == antiga.created_at
