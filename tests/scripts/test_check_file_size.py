"""Testes do limite de linhas por ficheiro."""
import check_file_size


def _make(tmp_path, name, lines):
    (tmp_path / name).write_text("x = 1\n" * lines, encoding="utf-8")


def test_ficheiro_de_301_linhas_falha(tmp_path):
    _make(tmp_path, "grande.py", 301)
    assert check_file_size.run(tmp_path, 200, 300) == 1


def test_ficheiro_de_300_linhas_passa(tmp_path):
    _make(tmp_path, "limite.py", 300)
    assert check_file_size.run(tmp_path, 200, 300) == 0


def test_pastas_geradas_sao_ignoradas(tmp_path):
    (tmp_path / ".venv").mkdir()
    _make(tmp_path / ".venv", "enorme.py", 900)
    assert check_file_size.run(tmp_path, 200, 300) == 0
