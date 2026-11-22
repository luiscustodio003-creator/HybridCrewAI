"""Impõe o limite de linhas por ficheiro (aviso aos 200, falha aos 300).

Uso: python scripts/check_file_size.py [--root CAMINHO] [--warn 200] [--fail 300]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import IGNORED_DIRS, ROOT, main_guard, report

EXTENSIONS = {".py", ".js", ".css", ".html", ".yaml", ".yml"}
EXEMPT_NAMES = {"tasks.yaml"}  # o plano é dados, não código


def iter_files(root: Path):
    """Percorre os ficheiros de código, ignorando pastas geradas."""
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        if path.is_file() and path.suffix in EXTENSIONS and path.name not in EXEMPT_NAMES:
            yield path


def run(root: Path, warn: int, fail: int) -> int:
    """Verifica todos os ficheiros e devolve o código de saída."""
    errors: list[str] = []
    warnings: list[str] = []
    for path in iter_files(root):
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        rel = path.relative_to(root)
        if lines > fail:
            errors.append(f"{rel}: {lines} linhas (máximo {fail})")
        elif lines > warn:
            warnings.append(f"{rel}: {lines} linhas (aviso aos {warn})")
    return report(errors, warnings, "check_file_size")


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--warn", type=int, default=200)
    parser.add_argument("--fail", type=int, default=300)
    args = parser.parse_args()
    return run(args.root, args.warn, args.fail)


if __name__ == "__main__":
    main_guard(cli)
