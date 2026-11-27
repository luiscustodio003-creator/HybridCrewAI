"""Testes de segurança da classificação e quarentena de anexos."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pytest

from app.workspace import (
    QuarantineError,
    QuarantineLimits,
    SensitiveReason,
    WorkspacePathError,
    classify_sensitive,
    quarantine_attachment,
    release_quarantine,
)

SEGREDO_FALSO = "sk-FALSO-NAO-REGISTAR"
CHAVE_FALSA = "AKIAFALSOFALSOFALSF"
TOKEN_OPACO = "token-opaco-de-teste"
LIMITES = QuarantineLimits(max_chars=240, max_file_bytes=1024)


def _workspace(tmp_path: Path) -> Path:
    """Cria a raiz de workspace usada pelos testes."""
    root = tmp_path / "workspace"
    root.mkdir()
    return root


def test_classificacao_sem_expor_conteudo(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    root = _workspace(tmp_path)
    (root / ".env").write_text(
        f"OPENAI_API_KEY={SEGREDO_FALSO}\nAWS_KEY={CHAVE_FALSA}\n", encoding="utf-8"
    )

    with caplog.at_level("DEBUG"):
        resultado = classify_sensitive(
            root, ".env", max_chars=240, max_file_bytes=1024
        )

    assert resultado.is_sensitive is True
    assert SensitiveReason.FILENAME in resultado.reasons
    assert SensitiveReason.CONTENT in resultado.reasons
    serializado = json.dumps(asdict(resultado))
    assert SEGREDO_FALSO not in serializado
    assert CHAVE_FALSA not in serializado
    assert SEGREDO_FALSO not in repr(resultado)
    assert CHAVE_FALSA not in repr(resultado)
    assert SEGREDO_FALSO not in caplog.text
    assert CHAVE_FALSA not in caplog.text


def test_anexo_fica_em_quarentena_ate_aprovacao(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = tmp_path / "anexo.txt"
    origem.write_text(SEGREDO_FALSO, encoding="utf-8")
    destino = root / "docs" / "anexo.txt"

    registro = quarantine_attachment(
        root,
        origem,
        relative_name="docs/anexo.txt",
        approval_token=TOKEN_OPACO,
        limits=LIMITES,
    )

    assert not destino.exists()
    assert (root / registro.quarantined_path).is_file()
    with pytest.raises(QuarantineError, match="aprovação"):
        release_quarantine(
            root, registro.id, approval_token="token-errado", limits=LIMITES
        )
    assert not destino.exists()
    libertado = release_quarantine(
        root, registro.id, approval_token=TOKEN_OPACO, limits=LIMITES
    )
    assert libertado == destino.resolve()
    assert destino.is_file()


def test_hash_do_anexo_em_quarentena_e_igual_ao_original(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = tmp_path / "anexo.bin"
    origem.write_bytes(b"conteudo-falso\n")

    registro = quarantine_attachment(
        root,
        origem,
        relative_name="anexos/anexo.bin",
        approval_token=TOKEN_OPACO,
        limits=LIMITES,
    )

    esperado = hashlib.sha256(origem.read_bytes()).hexdigest()
    assert registro.sha256 == esperado
    assert (
        hashlib.sha256((root / registro.quarantined_path).read_bytes()).hexdigest()
        == esperado
    )


def test_destino_com_travessia_e_rejeitado_antes_de_copiar(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = tmp_path / "anexo.txt"
    origem.write_text("x", encoding="utf-8")

    with pytest.raises(WorkspacePathError, match="travessia"):
        quarantine_attachment(
            root,
            origem,
            relative_name="../fora.txt",
            approval_token=TOKEN_OPACO,
            limits=LIMITES,
        )

    assert not (root / ".quarantine").exists()


def test_aprovacao_vazia_e_rejeitada(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    origem = tmp_path / "anexo.txt"
    origem.write_text("x", encoding="utf-8")

    with pytest.raises(QuarantineError, match="aprovação"):
        quarantine_attachment(
            root,
            origem,
            relative_name="anexo.txt",
            approval_token="",
            limits=LIMITES,
        )


def test_anexo_ligado_e_rejeitado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    externo = tmp_path / "externo"
    externo.mkdir()
    alvo = externo / "anexo.txt"
    alvo.write_text("x", encoding="utf-8")
    ligacao = root / "ligacao.txt"
    try:
        ligacao.symlink_to(alvo)
    except OSError:
        pytest.skip("o ambiente não permite criar symlinks")

    with patch.object(Path, "read_bytes", side_effect=AssertionError("leu ligação")):
        with pytest.raises(QuarantineError, match="ligação"):
            quarantine_attachment(
                root,
                ligacao,
                relative_name="anexo.txt",
                approval_token=TOKEN_OPACO,
                limits=LIMITES,
            )
