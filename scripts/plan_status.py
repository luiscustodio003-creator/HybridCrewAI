"""Mostra o progresso do plano e a próxima tarefa disponível.

Uso: python scripts/plan_status.py [--root CAMINHO]
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from _common import DONE_LIKE, ROOT, load_tasks, main_guard


def next_available(tasks: list[dict]) -> dict | None:
    """Primeira tarefa APPROVED ou PLANNED cujas dependências estão concluídas."""
    by_id = {t["id"]: t for t in tasks}
    for task in tasks:
        if task["status"] not in {"APPROVED", "IN_PROGRESS", "PLANNED", "NOT_STARTED"}:
            continue
        deps = task.get("depends_on", []) or []
        if all(by_id.get(dep, {}).get("status") in DONE_LIKE for dep in deps):
            return task
    return None


def run(root: Path) -> int:
    """Imprime o resumo por fase e a próxima tarefa."""
    data = load_tasks(root)
    tasks = data.get("tasks", [])
    phases = {p["id"]: p for p in data.get("phases", [])}
    print("Progresso por fase (VALIDATED/total):")
    for phase_id in sorted(phases):
        group = [t for t in tasks if t["phase"] == phase_id]
        done = sum(1 for t in group if t["status"] == "VALIDATED")
        print(f"  Fase {phase_id:02d} {phases[phase_id]['title'][:46]:<46} {done}/{len(group)}")
    counts = Counter(t["status"] for t in tasks)
    print("Estados:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    nxt = next_available(tasks)
    if nxt:
        print(f"Próxima tarefa: {nxt['id']} — {nxt['title']} [{nxt['status']}]")
    else:
        print("Próxima tarefa: nenhuma disponível (verifique bloqueios)")
    return 0


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    return run(parser.parse_args().root)


if __name__ == "__main__":
    main_guard(cli)
