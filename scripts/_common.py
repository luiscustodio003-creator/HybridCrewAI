"""Utilitários partilhados pelos scripts de controlo do HybridCrewAI."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

STATUSES = {
    "NOT_STARTED", "RESEARCH", "PLANNED", "APPROVED", "IN_PROGRESS", "BLOCKED",
    "IMPLEMENTED", "TESTING", "VALIDATED", "REJECTED", "DEPRECATED",
}
DONE_LIKE = {"IMPLEMENTED", "TESTING", "VALIDATED", "DEPRECATED"}
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
    ".ruff_cache", ".pytest_cache", "logs", "data", "reports", "projects",
}


def load_yaml(path: Path) -> dict:
    """Lê um ficheiro YAML e devolve um dicionário (vazio se o ficheiro não existir)."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_tasks(root: Path = ROOT) -> dict:
    """Lê o tasks.yaml da raiz do projecto."""
    return load_yaml(root / "tasks.yaml")


def report(errors: list[str], warnings: list[str], title: str) -> int:
    """Imprime o resultado de uma verificação e devolve o código de saída."""
    for item in warnings:
        print(f"  AVISO  {item}")
    for item in errors:
        print(f"  ERRO   {item}")
    verdict = "FALHOU" if errors else "OK"
    print(f"[{verdict}] {title}: {len(errors)} erro(s), {len(warnings)} aviso(s)")
    return 1 if errors else 0


def main_guard(func) -> None:
    """Executa func() e termina o processo com o código devolvido."""
    sys.exit(func())
