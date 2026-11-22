MÓDULO: core/tasks
FINALIDADE: Representar tarefas de forma imutável e aplicar uma máquina de estados que permita recuperação após interrupção.
FUNCIONALIDADES: identificadores UUIDv5 determinísticos; campos obrigatórios validados; transições explícitas; contagem de tentativas; marcas temporais em UTC.
ESTRUTURA: ids.py (generate_task_id); time.py (utc_now); model.py (Task, TaskSpec, new_task); state_machine.py (TaskStatus, TaskStateError, pode_transitar, transitar); __init__.py (API pública).
ESTADOS: created → queued → running → completed | failed | interrupted | cancelled; interrupted → queued | failed | cancelled. completed, failed e cancelled são terminais.
INTERFACE PÚBLICA: Task, TaskSpec, TaskStatus, TaskStateError, generate_task_id, new_task, pode_transitar, transitar, utc_now.
DEPENDÊNCIAS: apenas biblioteca padrão (dataclasses, datetime, enum, typing, uuid).
UTILIZAÇÃO: tarefa = new_task(TaskSpec(title='...', description='...', agent='...', phase='1', chave='HCW-XX-NNN')); tarefa = transitar(tarefa, TaskStatus.RUNNING).
TESTES: python -m pytest -q tests/unit/test_state_machine.py
LIMITAÇÕES: não persiste tarefas nem emite eventos; essas responsabilidades pertencem a HCW-01-008 e HCW-01-004.
RELAÇÕES: usado por core/results, core/persistence, runner e cli.
