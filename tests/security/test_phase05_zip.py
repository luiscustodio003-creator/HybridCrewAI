"""Testes de segurança da ingestão de ZIP no workspace."""

from __future__ import annotations

import io
import json
import stat
from dataclasses import asdict, replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

import pytest

from app.workspace import (
    ArchiveError,
    ArchiveLimits,
    ingest_zip,
)

LIMITES = ArchiveLimits(
    max_chars=240,
    max_file_bytes=1024,
    max_total_bytes=4096,
    max_zip_bytes=20_000,
    max_entries=8,
    max_ratio=10,
    max_nesting=1,
)


def _workspace(tmp_path: Path) -> Path:
    """Cria a raiz de workspace usada pelos testes."""
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def _criar_zip(
    caminho: Path,
    entradas: dict[str, bytes],
    *,
    compressao: int = ZIP_STORED,
    ligacoes: dict[str, str] | None = None,
) -> Path:
    """Cria um ZIP com ficheiros e, opcionalmente, entradas de ligação."""
    with ZipFile(caminho, "w", compressao) as arquivo:
        for nome, dados in entradas.items():
            arquivo.writestr(nome, dados)
        for nome, alvo in (ligacoes or {}).items():
            informacao = ZipInfo(nome)
            informacao.external_attr = (stat.S_IFLNK | 0o777) << 16
            arquivo.writestr(informacao, alvo)
    return caminho


def test_zip_slip_e_rejeitado_sem_extrair(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {"bom.txt": b" seguro ", "../fora.txt": b" ataque "},
    )

    with pytest.raises(ArchiveError, match="travessia"):
        ingest_zip(root, origem, destination="inbox", limits=LIMITES)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()
    assert not (tmp_path / "fora.txt").exists()


@pytest.mark.parametrize("nome", ["/etc/passwd", "C:\\Windows\\system32\\alvo.txt"])
def test_caminho_absoluto_e_rejeitado_sem_extrair(tmp_path: Path, nome: str) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(tmp_path / "entrada.zip", {nome: b" ataque "})

    with pytest.raises(ArchiveError, match="absoluto"):
        ingest_zip(root, origem, destination="inbox", limits=LIMITES)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()


def test_bomba_por_racio_e_rejeitada_antes_de_extrair(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {"bomba.txt": b"A" * 200_000},
        compressao=ZIP_DEFLATED,
    )
    limites = replace(LIMITES, max_file_bytes=1_000_000, max_total_bytes=1_000_000)

    with pytest.raises(ArchiveError, match="rácio"):
        ingest_zip(root, origem, destination="inbox", limits=limites)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()


def test_bomba_por_tamanho_total_e_rejeitada_antes_de_extrair(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {"a.txt": b"A" * 600, "b.txt": b"B" * 600},
    )
    limites = replace(LIMITES, max_total_bytes=1_000)

    with pytest.raises(ArchiveError, match="total"):
        ingest_zip(root, origem, destination="inbox", limits=limites)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()


def test_symlink_em_zip_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {},
        ligacoes={"ligacao.txt": "../fora.txt"},
    )

    with pytest.raises(ArchiveError, match="ligação"):
        ingest_zip(root, origem, destination="inbox", limits=LIMITES)

    assert not (root / "inbox").exists()
    assert not (tmp_path / "fora.txt").exists()


def test_zip_dentro_de_zip_alem_do_limite_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    interno = io.BytesIO()
    with ZipFile(interno, "w", ZIP_DEFLATED) as arquivo:
        arquivo.writestr("interno.txt", b" conteudo ")
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {"nivel1.zip": interno.getvalue()},
    )
    limites = replace(LIMITES, max_nesting=0)

    with pytest.raises(ArchiveError, match="aninhamento"):
        ingest_zip(root, origem, destination="inbox", limits=limites)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()


def test_numero_de_entradas_alem_do_limite_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {f"ficheiro-{indice}.txt": b"x" for indice in range(9)},
    )
    limites = replace(LIMITES, max_entries=8)

    with pytest.raises(ArchiveError, match="entradas"):
        ingest_zip(root, origem, destination="inbox", limits=limites)

    assert not (root / "inbox").exists()
    assert not (root / ".archive-staging").exists()


def test_zip_valido_e_extraido_com_relatorio_sem_conteudo(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    nota = b"conteudo innocuo\n"
    script = b"from pathlib import Path\nPath('EXECUTADO').touch()\n"
    origem = _criar_zip(
        tmp_path / "entrada.zip",
        {"docs/nota.txt": nota, "scripts/tarefa.py": script},
        compressao=ZIP_DEFLATED,
    )

    relatorio = ingest_zip(root, origem, destination="inbox", limits=LIMITES)

    assert (root / "inbox/docs/nota.txt").is_file()
    assert (root / "inbox/scripts/tarefa.py").is_file()
    assert not (root / "EXECUTADO").exists()
    assert relatorio.destination == "inbox"
    assert relatorio.total_bytes == len(nota) + len(script)
    serializado = json.dumps(asdict(relatorio))
    assert "conteudo innocuo" not in serializado
    assert "scripts/tarefa.py" in serializado
