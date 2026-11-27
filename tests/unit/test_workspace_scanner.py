"""Testes unitários do scanner de cobertura do workspace."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from app.workspace import (
    IgnoredFile,
    IgnoreReason,
    WorkspacePathError,
    scan_workspace,
)

TOTAL_FICHEIROS = 2


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


def test_scan_cobre_todos_os_ficheiros(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "b.md").write_text("b", encoding="utf-8")

    resultado = scan_workspace(root, max_chars=200, max_file_bytes=1024)

    assert resultado.total_on_disk == TOTAL_FICHEIROS
    assert resultado.readable == ("a.txt", "sub/b.md")
    assert resultado.ignored == ()
    assert resultado.coverage_complete is True


def test_ficheiro_grande_e_ignorado_com_motivo_estavel(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "pequeno.txt").write_text("x", encoding="utf-8")
    (root / "grande.bin").write_bytes(b"x" * 10)

    resultado = scan_workspace(root, max_chars=200, max_file_bytes=5)

    assert resultado.ignored == (IgnoredFile("grande.bin", IgnoreReason.TOO_LARGE),)
    assert [item.reason.value for item in resultado.ignored] == ["too-large"]
    assert resultado.total_on_disk == TOTAL_FICHEIROS
    assert len(resultado.readable) + len(resultado.ignored) == resultado.total_on_disk


def test_ligacao_externa_nao_e_listada(tmp_path: Path) -> None:
    externo = tmp_path / "externo"
    externo.mkdir()
    (externo / "segredo.txt").write_text("x", encoding="utf-8")
    root = _workspace(tmp_path)
    _ligar_directorio(root, "fora", externo)
    (root / "local.txt").write_text("x", encoding="utf-8")

    resultado = scan_workspace(root, max_chars=200, max_file_bytes=1024)

    nomes = set(resultado.readable) | {item.path for item in resultado.ignored}
    assert "fora/segredo.txt" not in nomes
    assert any(
        item.path == "fora" and item.reason is IgnoreReason.LINK
        for item in resultado.directories_ignored
    )
    assert resultado.readable == ("local.txt",)
    assert resultado.total_on_disk == 1


def test_conteudo_dos_ficheiros_nao_e_aberto(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "a.txt").write_text("x", encoding="utf-8")

    with patch("pathlib.Path.open", side_effect=AssertionError("abriu ficheiro")):
        resultado = scan_workspace(root, max_chars=200, max_file_bytes=1024)

    assert resultado.readable == ("a.txt",)


def test_ficheiro_ilegivel_e_ignorado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "a.txt").write_text("x", encoding="utf-8")
    lstat_real = os.lstat

    def lstat_com_falha(caminho: Any) -> os.stat_result:
        if Path(caminho).name == "a.txt":
            raise OSError("acesso negado")
        return lstat_real(caminho)

    with patch("app.workspace.scanner.os.lstat", side_effect=lstat_com_falha):
        resultado = scan_workspace(root, max_chars=200, max_file_bytes=1024)

    assert resultado.ignored == (IgnoredFile("a.txt", IgnoreReason.UNREADABLE),)


def test_limites_invalidos_sao_rejeitados(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    with pytest.raises(WorkspacePathError):
        scan_workspace(root, max_chars=0, max_file_bytes=10)

    with pytest.raises(WorkspacePathError):
        scan_workspace(root, max_chars=10, max_file_bytes=0)
