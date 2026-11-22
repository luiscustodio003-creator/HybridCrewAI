"""Testes da validação do tasks.yaml."""
import yaml

import validate_plan


def _write(tmp_path, tasks):
    (tmp_path / "tasks.yaml").write_text(yaml.safe_dump({"tasks": tasks}), encoding="utf-8")


def _task(**over):
    base = {"id": "HCW-00-001", "phase": 0, "status": "NOT_STARTED", "depends_on": []}
    base.update(over)
    return base


def test_plano_valido(tmp_path):
    _write(tmp_path, [_task()])
    assert validate_plan.run(tmp_path) == 0


def test_id_duplicado_falha(tmp_path):
    _write(tmp_path, [_task(), _task()])
    assert validate_plan.run(tmp_path) == 1


def test_estado_invalido_falha(tmp_path):
    _write(tmp_path, [_task(status="FEITO")])
    assert validate_plan.run(tmp_path) == 1


def test_validated_sem_evidencia_falha(tmp_path):
    _write(tmp_path, [_task(status="VALIDATED")])
    assert validate_plan.run(tmp_path) == 1


def test_dependencia_inexistente_falha(tmp_path):
    _write(tmp_path, [_task(depends_on=["HCW-09-009"])])
    assert validate_plan.run(tmp_path) == 1


def test_avancar_com_dependencia_por_concluir_falha(tmp_path):
    _write(tmp_path, [_task(), _task(id="HCW-00-002", status="IN_PROGRESS",
                                      depends_on=["HCW-00-001"], acceptance=["x"])])
    assert validate_plan.run(tmp_path) == 1
