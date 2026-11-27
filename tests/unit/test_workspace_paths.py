"""Testes unitários da validação de caminhos do workspace."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from app.workspace import WorkspacePathError, validate_workspace_path


def _workspace(tmp_path: Path) -> Path:
    """Cria uma raiz de workspace real para os testes."""
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


def test_caminho_simples_fica_dentro_da_raiz(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    resultado = validate_workspace_path(root, "src/main.py", max_chars=240)
    assert resultado == root / "src" / "main.py"
    assert resultado.is_relative_to(root.resolve())


@pytest.mark.skipif(os.name != "nt", reason="separador '\\' é exclusivo do Windows")
def test_caminho_com_separador_do_windows(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    resultado = validate_workspace_path(root, "src\\main.py", max_chars=240)
    assert resultado == root / "src" / "main.py"


@pytest.mark.parametrize(
    "candidate",
    ["/etc/passwd", "C:\\Windows\\system32", "\\\\servidor\\partilha\\ficheiro.txt"],
)
def test_caminho_absoluto_e_rejeitado(tmp_path: Path, candidate: str) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="absoluto"):
        validate_workspace_path(root, candidate, max_chars=240)


@pytest.mark.parametrize(
    "candidate", ["../fora.txt", "src/../../fora.txt", "src\\..\\fora.txt"]
)
def test_travessia_e_rejeitada(tmp_path: Path, candidate: str) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="travessia"):
        validate_workspace_path(root, candidate, max_chars=240)


@pytest.mark.parametrize(
    "candidate", ["CON", "con.txt", "AUX.log", "COM1", "LPT9.txt", "nul"]
)
def test_nomes_reservados_do_windows_sao_rejeitados(
    tmp_path: Path, candidate: str
) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="reservado"):
        validate_workspace_path(root, candidate, max_chars=240)


def test_caminho_longo_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    candidate = "a/" * 130 + "ficheiro.txt"
    with pytest.raises(WorkspacePathError, match="caracteres"):
        validate_workspace_path(root, candidate, max_chars=240)


def test_caminho_vazio_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="vazio"):
        validate_workspace_path(root, "   ", max_chars=240)


def test_raiz_inexistente_e_rejeitada(tmp_path: Path) -> None:
    root = tmp_path / "sem-raiz"
    with pytest.raises(WorkspacePathError, match="raiz"):
        validate_workspace_path(root, "ficheiro.txt", max_chars=240)


def test_limite_invalido_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(WorkspacePathError, match="max_chars"):
        validate_workspace_path(root, "ficheiro.txt", max_chars=0)


def test_ligacao_para_fora_e_rejeitada(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    fora = tmp_path / "fora"
    fora.mkdir()
    _ligar_directorio(root, "ligacao", fora)
    with pytest.raises(WorkspacePathError, match="ligação"):
        validate_workspace_path(root, "ligacao/ficheiro.txt", max_chars=240)
