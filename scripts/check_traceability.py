"""Verifica a rastreabilidade: requisito -> tarefa -> teste -> evidência.

Uso: python scripts/check_traceability.py [--root CAMINHO]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import ROOT, load_tasks, load_yaml, main_guard, report


def run(root: Path) -> int:
    """Cruza requirements.yaml com tasks.yaml e o disco."""
    tasks = load_tasks(root).get("tasks", [])
    requirements = load_yaml(root / "docs" / "requirements.yaml").get("requirements", [])
    errors: list[str] = []
    warnings: list[str] = []
    known = {r["id"] for r in requirements}
    covered: set[str] = set()
    for task in tasks:
        for req in task.get("requirements", []) or []:
            covered.add(req)
            if req not in known:
                errors.append(f"{task['id']}: requisito '{req}' não existe em requirements.yaml")
        if task["status"] == "VALIDATED":
            for test in task.get("tests", []) or []:
                if not (root / test).exists():
                    errors.append(f"{task['id']}: teste '{test}' não existe no disco")
            for ev in task.get("evidence", []) or []:
                if not (root / ev).exists():
                    errors.append(f"{task['id']}: evidência '{ev}' não existe no disco")
    for req in sorted(known - covered):
        warnings.append(f"{req}: sem nenhuma tarefa associada")
    return report(errors, warnings, "check_traceability")


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    return run(parser.parse_args().root)


if __name__ == "__main__":
    main_guard(cli)
