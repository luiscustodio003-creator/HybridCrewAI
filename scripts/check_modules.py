"""Verifica que cada módulo em app/ tem README.txt e module.yaml.

Uso: python scripts/check_modules.py [--root CAMINHO] [--warn-only]
Um módulo é uma pasta de app/ que contém ficheiros .py directamente.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import IGNORED_DIRS, ROOT, load_yaml, main_guard, report

REQUIRED_KEYS = {"name", "purpose", "public_api", "depends_on"}


def find_modules(app: Path):
    """Devolve as pastas que contêm código Python directamente."""
    for folder in sorted(p for p in app.rglob("*") if p.is_dir()):
        if any(part in IGNORED_DIRS for part in folder.relative_to(app).parts):
            continue
        if any(f.suffix == ".py" and f.name != "__init__.py" for f in folder.iterdir()):
            yield folder


def run(root: Path, warn_only: bool) -> int:
    """Verifica a documentação de cada módulo."""
    app = root / "app"
    errors: list[str] = []
    warnings: list[str] = []
    if not app.exists():
        return report(errors, ["pasta app/ ainda não existe"], "check_modules")
    target = warnings if warn_only else errors
    for module in find_modules(app):
        rel = module.relative_to(root)
        if not (module / "README.txt").exists():
            target.append(f"{rel}: falta README.txt")
        manifest = module / "module.yaml"
        if not manifest.exists():
            target.append(f"{rel}: falta module.yaml")
            continue
        missing = REQUIRED_KEYS - set(load_yaml(manifest))
        if missing:
            target.append(f"{rel}: module.yaml sem as chaves {sorted(missing)}")
    return report(errors, warnings, "check_modules")


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()
    return run(args.root, args.warn_only)


if __name__ == "__main__":
    main_guard(cli)
