"""Testes de ataque aos caminhos do workspace."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.workspace import WorkspacePathError, validate_workspace_path


def _workspace(tmp_path: Path) -> Path:
    """Cria a raiz e um directório externo para simular ataques."""
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _ligar_directorio(raiz: Path, nome: str, alvo: Path) -> Path:
    """Cria uma ligação de directório, com junction como alternativa no Windows."""
    ligacao = raiz / nome
    try:
        ligacao.symlink_to(alvo, target_is_directory=True)
        return ligacao
    except OSError:
        resultado = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(ligacao), str(alvo)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    if resultado.returncode != 0:
        pytest.skip("o ambiente não permite criar symlinks nem junctions")
    return ligacao


def test_ligacao_externa_e_rejeitada_antes_de_abrir(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    fora = tmp_path / "fora"
    fora.mkdir()
    alvo = fora / "chave-falsa.txt"
    alvo.write_text("sk-FALSO-NAO-GRAVAR", encoding="utf-8")
    _ligar_directorio(root, "externo", fora)
    with patch.object(Path, "open", side_effect=AssertionError("abriu ficheiro")):
        with pytest.raises(WorkspacePathError, match="ligação"):
            validate_workspace_path(root, "externo/chave-falsa.txt", max_chars=240)


@pytest.mark.skipif(os.name != "nt", reason="junction é exclusiva do Windows")
def test_junction_externa_e_rejeitada(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    fora = tmp_path / "fora"
    fora.mkdir()
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(root / "junção"), str(fora)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("o ambiente não permite criar junctions")
    with pytest.raises(WorkspacePathError, match="ligação|reparse"):
        validate_workspace_path(root, "junção/ficheiro.txt", max_chars=240)


def test_ataque_de_caminho_absoluto_do_windows(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="absoluto"):
        validate_workspace_path(root, "C:\\Windows\\system32\\drivers", max_chars=240)


def test_ataque_de_travessia_com_separadores_misturados(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="travessia"):
        validate_workspace_path(root, "src\\..\\..\\fora.txt", max_chars=240)


def test_ataque_de_caminho_longo_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="caracteres"):
        validate_workspace_path(root, "a/" * 200 + "ficheiro.txt", max_chars=240)


def test_caminho_final_valido_pertence_a_raiz_resolvida(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "src").mkdir()
    resultado = validate_workspace_path(root, "src/ficheiro.txt", max_chars=240)
    assert resultado.is_relative_to(root.resolve())
