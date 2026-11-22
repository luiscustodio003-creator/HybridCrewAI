"""Valida o tasks.yaml: estados, IDs, dependências e evidências.

Uso: python scripts/validate_plan.py [--root CAMINHO]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import DONE_LIKE, ROOT, STATUSES, load_tasks, main_guard, report

ID_PATTERN = re.compile(r"^HCW-(\d{2})-(\d{3})$")


def check_task(task: dict, ids: set[str], errors: list[str], warnings: list[str]) -> None:
    """Valida uma tarefa individual."""
    tid = str(task.get("id", "?"))
    match = ID_PATTERN.match(tid)
    if not match:
        errors.append(f"{tid}: identificador fora do formato HCW-FF-NNN")
    elif int(match.group(1)) != task.get("phase"):
        errors.append(f"{tid}: a fase do ID não coincide com o campo phase")
    status = task.get("status")
    if status not in STATUSES:
        errors.append(f"{tid}: estado inválido '{status}'")
    for dep in task.get("depends_on", []) or []:
        if dep not in ids:
            errors.append(f"{tid}: depende de '{dep}', que não existe")
    if status == "VALIDATED":
        if not task.get("evidence"):
            errors.append(f"{tid}: VALIDATED sem evidência")
        if not task.get("validated_on"):
            errors.append(f"{tid}: VALIDATED sem validated_on")
    if status in {"IN_PROGRESS", "IMPLEMENTED", "TESTING"} and not task.get("acceptance"):
        warnings.append(f"{tid}: sem critérios de aceitação")


def check_dependency_order(tasks: list[dict], errors: list[str]) -> None:
    """Uma tarefa só pode avançar se as dependências estiverem concluídas."""
    by_id = {t["id"]: t for t in tasks}
    for task in tasks:
        if task.get("status") not in {"IN_PROGRESS", "IMPLEMENTED", "TESTING", "VALIDATED"}:
            continue
        for dep in task.get("depends_on", []) or []:
            dep_status = by_id.get(dep, {}).get("status")
            if dep_status not in DONE_LIKE:
                errors.append(f"{task['id']}: avançou mas '{dep}' está em {dep_status}")


def run(root: Path) -> int:
    """Executa todas as verificações do plano."""
    data = load_tasks(root)
    tasks = data.get("tasks", [])
    errors: list[str] = []
    warnings: list[str] = []
    if not tasks:
        errors.append("tasks.yaml não tem tarefas")
    ids = [t.get("id") for t in tasks]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"{dup}: identificador duplicado")
    for task in tasks:
        check_task(task, set(ids), errors, warnings)
    check_dependency_order(tasks, errors)
    return report(errors, warnings, "validate_plan")


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    return run(parser.parse_args().root)


if __name__ == "__main__":
    main_guard(cli)
