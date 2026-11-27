"""Integração de snapshots, rollback e undo do workspace."""

from __future__ import annotations

import hashlib
import json
import subprocess
from importlib import import_module
from pathlib import Path

import pytest

from app.workspace import (
    RollbackError,
    SnapshotError,
    SnapshotLimits,
    create_snapshot,
    load_snapshot,
    rollback,
    snapshot_digest,
    undo_rollback,
)

modulo_rollback = import_module("app.workspace.rollback")


def _limites() -> SnapshotLimits:
    """Devolve limites pequenos e suficientes para os testes."""
    return SnapshotLimits(
        max_chars=240,
        max_file_bytes=100_000,
        max_total_bytes=1_000_000,
        max_files=100,
    )


def _sha256(caminho: Path) -> str:
    """Calcula o SHA-256 de um ficheiro de teste."""
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _preparar_workspace(tmp_path: Path) -> Path:
    """Cria um workspace com ficheiros em subpastas."""
    raiz = tmp_path / "workspace"
    (raiz / "src").mkdir(parents=True)
    (raiz / "docs").mkdir()
    (raiz / "src" / "main.py").write_text("print('original')\n", encoding="utf-8")
    (raiz / "README.txt").write_text("projecto de teste\n", encoding="utf-8")
    (raiz / "docs" / "notas.txt").write_text("notas originais\n", encoding="utf-8")
    return raiz


def _hashes_do_workspace(raiz: Path) -> dict[str, str]:
    """Devolve os hashes dos ficheiros normais do workspace."""
    ignorados = {".snapshots", ".snapshot-staging", ".rollback-staging"}
    return {
        caminho.relative_to(raiz).as_posix(): _sha256(caminho)
        for caminho in sorted(raiz.rglob("*"))
        if caminho.is_file() and not set(caminho.relative_to(raiz).parts) & ignorados
    }


def test_snapshot_alteracao_e_rollback_devolvem_hashes_identicos(
    tmp_path: Path,
) -> None:
    """O rollback repõe byte a byte o estado guardado no snapshot."""
    raiz = _preparar_workspace(tmp_path)
    originais = _hashes_do_workspace(raiz)

    instantaneo = create_snapshot(raiz, limits=_limites())
    (raiz / "src" / "main.py").write_text("print('alterado')\n", encoding="utf-8")
    (raiz / "novo.txt").write_text("ficheiro novo\n", encoding="utf-8")
    (raiz / "README.txt").unlink()

    relatado = rollback(raiz, instantaneo.id, limits=_limites())

    assert relatado.restored_digest == instantaneo.digest
    assert relatado.restored_digest == snapshot_digest(instantaneo.entries)
    assert _hashes_do_workspace(raiz) == originais
    assert (raiz / "src" / "main.py").read_text(encoding="utf-8") == "print('original')\n"
    assert (raiz / "README.txt").exists()
    assert not (raiz / "novo.txt").exists()


def test_undo_repoe_estado_pos_alteracao(tmp_path: Path) -> None:
    """O undo desfaz o rollback e recupera o estado alterado."""
    raiz = _preparar_workspace(tmp_path)
    instantaneo = create_snapshot(raiz, limits=_limites())

    (raiz / "src" / "main.py").write_text("print('alterado')\n", encoding="utf-8")
    (raiz / "novo.txt").write_text("ficheiro novo\n", encoding="utf-8")
    antes_do_undo = _hashes_do_workspace(raiz)

    relatado = rollback(raiz, instantaneo.id, limits=_limites())
    desfeito = undo_rollback(raiz, relatado.undo_id, limits=_limites())

    assert desfeito.restored_digest == snapshot_digest(
        load_snapshot(raiz, relatado.undo_id, limits=_limites()).entries
    )
    assert _hashes_do_workspace(raiz) == antes_do_undo


def test_interrupcao_antes_do_commit_nao_deixa_parciais_e_preserva_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uma falha antes do commit não altera o workspace nem perde o snapshot."""
    raiz = _preparar_workspace(tmp_path)
    instantaneo = create_snapshot(raiz, limits=_limites())
    (raiz / "src" / "main.py").write_text("print('alterado')\n", encoding="utf-8")
    estado = _hashes_do_workspace(raiz)

    def interromper(origem: Path, destino: Path) -> None:
        """Simula uma interrupção antes de substituir o primeiro ficheiro."""
        raise OSError("interrupcao simulada")

    monkeypatch.setattr(modulo_rollback, "_substituir", interromper)
    with pytest.raises(RollbackError):
        rollback(raiz, instantaneo.id, limits=_limites())

    assert _hashes_do_workspace(raiz) == estado
    assert (raiz / "src" / "main.py").read_text(encoding="utf-8") == "print('alterado')\n"
    assert load_snapshot(raiz, instantaneo.id, limits=_limites()).id == instantaneo.id
    assert not any(caminho.name.startswith(".rollback-staging") for caminho in raiz.iterdir())


def test_snapshot_adulterado_e_recusado(tmp_path: Path) -> None:
    """Um ficheiro alterado dentro do snapshot invalida o rollback."""
    raiz = _preparar_workspace(tmp_path)
    instantaneo = create_snapshot(raiz, limits=_limites())
    alvo = raiz / ".snapshots" / instantaneo.id / "src" / "main.py"
    alvo.write_text("conteudo forjado\n", encoding="utf-8")

    with pytest.raises(SnapshotError):
        load_snapshot(raiz, instantaneo.id, limits=_limites())
    with pytest.raises(RollbackError):
        rollback(raiz, instantaneo.id, limits=_limites())


def test_identificador_de_snapshot_com_travessia_e_recusado(tmp_path: Path) -> None:
    """Identificadores não hexadecimais não podem virar caminhos."""
    raiz = _preparar_workspace(tmp_path)
    with pytest.raises(RollbackError):
        rollback(raiz, "../.snapshots", limits=_limites())


def test_manifest_com_travessia_e_recusado(tmp_path: Path) -> None:
    """Um manifesto forjado não pode apontar para fora do snapshot."""
    raiz = _preparar_workspace(tmp_path)
    instantaneo = create_snapshot(raiz, limits=_limites())
    caminho = raiz / ".snapshots" / instantaneo.id / "manifest.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["entries"][0]["path"] = "../fora.txt"
    caminho.write_text(json.dumps(dados), encoding="utf-8")

    with pytest.raises(SnapshotError):
        load_snapshot(raiz, instantaneo.id, limits=_limites())


def test_snapshot_nao_inclui_ligacao_para_fora(tmp_path: Path) -> None:
    """Junctions para fora do workspace não entram no snapshot."""
    raiz = _preparar_workspace(tmp_path)
    externa = tmp_path / "externa"
    externa.mkdir()
    (externa / "segredo.txt").write_text("fora do workspace\n", encoding="utf-8")
    ligacao = raiz / "ligacao"

    resultado = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(ligacao), str(externa)],
        capture_output=True,
        check=False,
    )
    if resultado.returncode != 0:
        pytest.skip("Este ambiente não permite criar junctions.")

    instantaneo = create_snapshot(raiz, limits=_limites())

    assert all(not entrada.path.startswith("ligacao/") for entrada in instantaneo.entries)
    assert not (raiz / ".snapshots" / instantaneo.id / "ligacao").exists()
