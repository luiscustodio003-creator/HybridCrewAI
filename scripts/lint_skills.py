"""Valida as Skills: frontmatter, nome, tamanho e referências existentes.

Uso: python scripts/lint_skills.py [--root CAMINHO] [--max-lines 100]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from _common import ROOT, main_guard, report

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REF_PATTERN = re.compile(r"`((?:references|templates|scripts)/[^`\s]+)`")


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Separa o frontmatter YAML do corpo; devolve ({}, texto) se não existir."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return (yaml.safe_load(parts[1]) or {}), parts[2]


def check_skill(skill_dir: Path, root: Path, max_lines: int,
                errors: list[str], warnings: list[str]) -> None:
    """Valida uma Skill individual."""
    skill_file = skill_dir / "SKILL.md"
    name = skill_dir.name
    if not skill_file.exists():
        errors.append(f"{name}: falta SKILL.md (em maiúsculas)")
        return
    text = skill_file.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    if meta.get("name") != name:
        errors.append(f"{name}: 'name' do frontmatter tem de ser igual à pasta")
    if not NAME_PATTERN.match(name) or len(name) > 64:
        errors.append(f"{name}: nome inválido (minúsculas, números e hífens)")
    description = str(meta.get("description", "")).strip()
    if not 60 <= len(description) <= 1024:
        errors.append(f"{name}: description deve ter entre 60 e 1024 caracteres")
    lines = len(text.splitlines())
    if lines > max_lines:
        errors.append(f"{name}: SKILL.md com {lines} linhas (máximo {max_lines})")
    for ref in REF_PATTERN.findall(body):
        if not (skill_dir / ref).exists() and not (root / ref).exists():
            warnings.append(f"{name}: referência '{ref}' não encontrada")


def run(root: Path, max_lines: int) -> int:
    """Valida todas as Skills em .opencode/skills/ (ou skills/)."""
    errors: list[str] = []
    warnings: list[str] = []
    skills = root / ".opencode" / "skills"
    if not skills.exists():
        skills = root / "skills"
    dirs = sorted(p for p in skills.iterdir() if p.is_dir()) if skills.exists() else []
    if not dirs:
        errors.append("não existem Skills em .opencode/skills/")
    for skill_dir in dirs:
        check_skill(skill_dir, root, max_lines, errors, warnings)
    return report(errors, warnings, f"lint_skills ({len(dirs)} Skills)")


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--max-lines", type=int, default=100)
    args = parser.parse_args()
    return run(args.root, args.max_lines)


if __name__ == "__main__":
    main_guard(cli)
