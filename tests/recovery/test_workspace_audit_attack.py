"""Ataques ao journal e às directórias internas do workspace."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from app.core.events import EventContext
from app.workspace import AuditLimits, AuditTrail, FileChange, FileOpLimits, journal
from app.workspace.file_ops import FileOpsError, apply_atomic, recover_workspace

CONTEXTO = EventContext(
    correlation_id="correlacao-ataque-008",
    task_id="HCW-05-008",
    agent="teste",
    phase="5",
)


def _limites() -> FileOpLimits:
    """Devolve limites pequenos e suficientes para os testes."""
    return FileOpLimits(
        max_chars=240,
        max_file_bytes=1000,
        max_total_bytes=10000,
        max_files=10,
    )


def _auditoria(raiz: Path) -> AuditTrail:
    """Cria a auditoria do workspace de teste."""
    return AuditTrail(
        raiz,
        limits=AuditLimits(max_chars=240, max_audit_bytes=1_000_000),
    )


def _preparar(tmp_path: Path) -> Path:
    """Cria um workspace isolado para cada teste."""
    raiz = tmp_path / "workspace"
    raiz.mkdir()
    return raiz


def test_journal_adulterado_e_recusado(tmp_path: Path) -> None:
    """Um manifesto com digest forjado não altera o workspace."""
    raiz = _preparar(tmp_path)
    (raiz / "estado.txt").write_bytes(b"original")
    operacao = "a" * 32
    limites = _limites()
    manifesto = journal.novo_manifest(
        raiz,
        operacao,
        ({"path": "estado.txt", "size": 4, "sha256": hashlib.sha256(b"novo").hexdigest()},),
        limites,
    )
    manifesto["digest"] = "b" * 64
    confirmado = raiz / ".file-ops" / "journal" / "committed"
    confirmado.mkdir(parents=True)
    (confirmado / f"{operacao}.json").write_text(
        json.dumps(manifesto, sort_keys=True), encoding="utf-8"
    )
    staging = raiz / ".file-ops" / "staging" / operacao
    staging.mkdir(parents=True)
    (staging / "estado.txt").write_bytes(b"novo")

    with pytest.raises(FileOpsError):
        recover_workspace(
            raiz,
            context=CONTEXTO,
            audit=_auditoria(raiz),
            limits=limites,
        )

    assert (raiz / "estado.txt").read_bytes() == b"original"


def test_manifesto_do_journal_nao_guarda_conteudo(tmp_path: Path) -> None:
    """O journal guarda apenas metadados, nunca o conteúdo da escrita."""
    raiz = _preparar(tmp_path)
    dados = b"sk-chave-falsa-para-teste"
    manifesto = journal.novo_manifest(
        raiz,
        "c" * 32,
        ({
            "path": "segredo.txt",
            "size": len(dados),
            "sha256": hashlib.sha256(dados).hexdigest(),
            "data": dados,
        },),
        _limites(),
    )

    texto = json.dumps(manifesto, sort_keys=True)

    objeto = cast("dict[str, object]", json.loads(texto))
    entradas = cast("list[dict[str, object]]", objeto["files"])
    assert "sk-" not in texto
    assert entradas[0]["path"] == "segredo.txt"


def test_escrita_em_pasta_interna_e_recusada(tmp_path: Path) -> None:
    """O journal e o registo não podem ser destino de uma escrita."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)
    alvo = raiz / ".file-ops" / "audit.jsonl"
    alvo.parent.mkdir()

    with pytest.raises(FileOpsError):
        apply_atomic(
            raiz,
            (FileChange(path=".file-ops/audit.jsonl", data=b"adulterado"),),
            context=CONTEXTO,
            audit=auditoria,
            limits=_limites(),
        )

    assert not alvo.exists()
