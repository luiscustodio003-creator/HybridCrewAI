"""Testes da verificação de documentação dos módulos."""
import check_modules

MANIFEST = "name: m\npurpose: p\npublic_api: [f]\ndepends_on: []\n"


def _module(tmp_path, readme=True, manifest=True):
    folder = tmp_path / "app" / "core" / "mod"
    folder.mkdir(parents=True)
    (folder / "codigo.py").write_text("x = 1\n", encoding="utf-8")
    if readme:
        (folder / "README.txt").write_text("MÓDULO: m\n", encoding="utf-8")
    if manifest:
        (folder / "module.yaml").write_text(MANIFEST, encoding="utf-8")


def test_modulo_completo_passa(tmp_path):
    _module(tmp_path)
    assert check_modules.run(tmp_path, warn_only=False) == 0


def test_modulo_sem_readme_falha(tmp_path):
    _module(tmp_path, readme=False)
    assert check_modules.run(tmp_path, warn_only=False) == 1


def test_modulo_sem_manifesto_so_avisa_em_modo_warn_only(tmp_path):
    _module(tmp_path, manifest=False)
    assert check_modules.run(tmp_path, warn_only=True) == 0


def test_sem_pasta_app_nao_falha(tmp_path):
    assert check_modules.run(tmp_path, warn_only=False) == 0
