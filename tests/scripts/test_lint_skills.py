"""Testes da validação das Skills."""
from pathlib import Path

import lint_skills

REAL_ROOT = Path(__file__).resolve().parents[2]
GOOD = "---\nname: {n}\ndescription: {d}\n---\n# T\ncorpo\n"
DESC = "Descrição suficientemente longa para cumprir o mínimo de sessenta caracteres exigido."


def _skill(root, name, text):
    folder = root / "skills" / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(text, encoding="utf-8")


def test_skills_reais_do_projecto_passam():
    assert lint_skills.run(REAL_ROOT, 100) == 0


def test_skill_valida(tmp_path):
    _skill(tmp_path, "hcw-teste", GOOD.format(n="hcw-teste", d=DESC))
    assert lint_skills.run(tmp_path, 100) == 0


def test_sem_frontmatter_falha(tmp_path):
    _skill(tmp_path, "hcw-teste", "# sem frontmatter\n")
    assert lint_skills.run(tmp_path, 100) == 1


def test_nome_diferente_da_pasta_falha(tmp_path):
    _skill(tmp_path, "hcw-teste", GOOD.format(n="outro-nome", d=DESC))
    assert lint_skills.run(tmp_path, 100) == 1


def test_skill_demasiado_longa_falha(tmp_path):
    _skill(tmp_path, "hcw-teste", GOOD.format(n="hcw-teste", d=DESC) + "linha\n" * 120)
    assert lint_skills.run(tmp_path, 100) == 1
