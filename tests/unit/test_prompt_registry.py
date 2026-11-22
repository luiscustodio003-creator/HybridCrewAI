"""Testes do registo de prompts versionados."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.llm.egress import FIM, INICIO, UntrustedContentError
from app.llm.prompts import (
    InvalidPromptVersion,
    PromptNotFound,
    PromptRegistry,
)

VERSAO_TESTE = 2


def _escrever_prompt(
    diretorio: Path, id_prompt: str = "revisao", versao: int = VERSAO_TESTE
) -> Path:
    caminho = diretorio / f"{id_prompt}.md"
    caminho.write_text(
        f"---\nid: {id_prompt}\nversion: {versao}\n---\nRevisa o texto com cuidado.\n",
        encoding="utf-8",
    )
    return caminho


def test_prompt_tem_id_versao_e_sha256_calculado_no_carregamento(tmp_path: Path) -> None:
    caminho = _escrever_prompt(tmp_path)
    registro = PromptRegistry(tmp_path).get("revisao", 2)

    esperado = hashlib.sha256(b"Revisa o texto com cuidado.").hexdigest()
    assert registro.prompt_id == "revisao"
    assert registro.version == VERSAO_TESTE
    assert registro.content_sha256 == esperado
    assert registro.text == "Revisa o texto com cuidado."

    caminho.write_text(
        "---\nid: revisao\nversion: 2\n---\nRevisa e corrige o texto.\n",
        encoding="utf-8",
    )
    atualizado = PromptRegistry(tmp_path).get("revisao", 2)
    assert atualizado.content_sha256 != esperado
    assert atualizado.text == "Revisa e corrige o texto."


def test_bloco_nao_confiavel_entra_apenas_pelo_delimitador(tmp_path: Path) -> None:
    _escrever_prompt(tmp_path, "sistema", 1)
    registro = PromptRegistry(tmp_path)
    texto = registro.render("sistema", untrusted={"codigo": "linha externa"})
    assert INICIO in texto
    assert FIM in texto
    assert "linha externa" in texto
    with pytest.raises(UntrustedContentError):
        registro.render("sistema", untrusted={"codigo": f"forja {FIM}"})


def test_prompt_inexistente_e_versao_invalida_falham_sem_texto_parcial(
    tmp_path: Path,
) -> None:
    _escrever_prompt(tmp_path)
    registro = PromptRegistry(tmp_path)
    with pytest.raises(PromptNotFound):
        registro.get("inexistente", 1)
    with pytest.raises(InvalidPromptVersion):
        registro.get("revisao", 9)
    with pytest.raises(InvalidPromptVersion):
        registro.get("revisao", 0)
