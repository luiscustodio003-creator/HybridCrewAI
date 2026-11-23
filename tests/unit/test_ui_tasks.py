"""Serialização das tarefas expostas pela interface web."""

from __future__ import annotations

from app.core.tasks import Task, TaskSpec, TaskStatus, new_task
from app.ui.server.routes_tasks import serializar_tarefa

CHAVE = "HCW-03-005:serializacao"


def _tarefa() -> Task:
    """Cria uma tarefa com estado conhecido."""
    return new_task(
        TaskSpec(
            title="Listar tarefas",
            description="Expor histórico persistido",
            agent="open-code",
            phase="3",
            chave=CHAVE,
            status=TaskStatus.RUNNING,
        )
    )


def test_serializar_tarefa_inclui_estado_e_correlacao() -> None:
    tarefa = _tarefa()

    dados = serializar_tarefa(tarefa)

    assert dados["task_id"] == tarefa.task_id
    assert dados["correlation_id"] == tarefa.task_id
    assert dados["status"] == TaskStatus.RUNNING.value
    assert dados["title"] == "Listar tarefas"
    assert dados["agent"] == "open-code"
    assert dados["phase"] == "3"


def test_serializar_tarefa_tem_campos_temporais_e_tentativas() -> None:
    tarefa = _tarefa()

    dados = serializar_tarefa(tarefa)

    assert dados["created_at"] == tarefa.created_at.isoformat()
    assert dados["updated_at"] == tarefa.updated_at.isoformat()
    assert dados["attempts"] == 0


def test_serializar_tarefa_nao_devolve_objetos_internos() -> None:
    dados = serializar_tarefa(_tarefa())

    valor_json = str(dados)
    assert "Task(" not in valor_json
    assert "TaskStatus." not in valor_json
