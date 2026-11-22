"""Gate de uma fase: verificações + testes acumulados -> GO / NO-GO.

Uso: python scripts/run_gate.py --phase N [--root CAMINHO]
Escreve reports/phase-NN/report.json e report.md. GO só se tudo passar.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from _common import ROOT, load_tasks, main_guard

CHECKS = [
    ("validate_plan", ["scripts/validate_plan.py"]),
    ("check_file_size", ["scripts/check_file_size.py"]),
    ("check_modules", ["scripts/check_modules.py"]),
    ("lint_skills", ["scripts/lint_skills.py"]),
    ("check_traceability", ["scripts/check_traceability.py"]),
]


def run_cmd(args: list[str], root: Path) -> tuple[int, str]:
    """Executa um comando e devolve (código, saída)."""
    proc = subprocess.run(args, cwd=root, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def cumulative_tests(tasks: list[dict], phase: int, root: Path) -> list[str]:
    """Ficheiros de teste de todas as tarefas das fases <= phase que existem em disco."""
    files: list[str] = []
    for task in tasks:
        if task["phase"] <= phase:
            for test in task.get("tests", []) or []:
                if (root / test).exists() and test not in files:
                    files.append(test)
    return files


def pending_tasks(tasks: list[dict], phase: int) -> list[str]:
    """Tarefas da fase (excepto o gate) que ainda não foram implementadas."""
    open_states = {"NOT_STARTED", "RESEARCH", "PLANNED", "APPROVED", "IN_PROGRESS", "BLOCKED"}
    return [t["id"] for t in tasks
            if t["phase"] == phase and t["status"] in open_states and not t["id"].endswith("999")]


def run(root: Path, phase: int) -> int:
    """Corre o gate e grava o relatório."""
    tasks = load_tasks(root).get("tasks", [])
    results = []
    for name, cmd in CHECKS:
        code, output = run_cmd([sys.executable, *cmd], root)
        results.append({"check": name, "ok": code == 0, "output": output[-1500:]})
    test_files = cumulative_tests(tasks, phase, root)
    if test_files:
        code, output = run_cmd([sys.executable, "-m", "pytest", "-q", *test_files], root)
        results.append({"check": f"pytest ({len(test_files)} ficheiros)", "ok": code == 0,
                        "output": output[-3000:]})
    else:
        results.append({"check": "pytest", "ok": False,
                        "output": "nenhum ficheiro de teste das tarefas existe em disco"})
    pending = pending_tasks(tasks, phase)
    results.append({"check": "tarefas da fase concluídas", "ok": not pending,
                    "output": f"pendentes: {pending}" if pending else "todas concluídas"})
    go = all(r["ok"] for r in results)
    out = root / "reports" / f"phase-{phase:02d}"
    out.mkdir(parents=True, exist_ok=True)
    payload = {"phase": phase, "verdict": "GO" if go else "NO-GO",
               "when": datetime.now().isoformat(timespec="seconds"), "results": results}
    (out / "report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
    lines = [f"# Gate da Fase {phase:02d} — {payload['verdict']}", f"Data: {payload['when']}", ""]
    for r in results:
        lines.append(f"- {'OK  ' if r['ok'] else 'FALHA'} {r['check']}")
    (out / "report.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))
    print(f"Relatório: {out / 'report.md'}")
    return 0 if go else 1


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return run(args.root, args.phase)


if __name__ == "__main__":
    main_guard(cli)
