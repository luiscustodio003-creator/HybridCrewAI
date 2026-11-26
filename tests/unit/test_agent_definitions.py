from __future__ import annotations

from pathlib import Path

import pytest
from agents.definitions import (
    DefinitionError,
    load_agent_definitions,
    parse_agent_definition,
    render_prompt,
)

from app.llm.egress import FIM, INICIO, UntrustedContentError

RAIZ = Path(__file__).resolve().parents[2]
PASTA_DEFINICOES = RAIZ / "agents" / "definitions"
IDS_ESPERADOS = {"planeador", "arquitecto", "implementador", "revisor", "relator"}
CONTEUDO_VALIDO = """---
id: teste
nome: Agente de teste
versao: 1
entrada: texto
saida: texto
ferramentas: leitura
---
Instrução determinística.
"""


def test_definicoes_tem_cabecalho_obrigatorio() -> None:
    definicoes = load_agent_definitions(PASTA_DEFINICOES)
    assert len(definicoes) == len(IDS_ESPERADOS)
    assert {definicao.agent_id for definicao in definicoes} == IDS_ESPERADOS
    for definicao in definicoes:
        assert definicao.nome
        assert definicao.versao == 1
        assert definicao.entrada
        assert definicao.saida
        assert definicao.ferramentas
        assert definicao.texto


def test_cabecalho_invalido_e_recusado_com_mensagem_clara(tmp_path: Path) -> None:
    caminho = tmp_path / "invalido.md"
    caminho.write_text(
        "---\nid: invalido\nnome: Invalido\nversao: 1\nentrada: texto\n"
        "saida: texto\n---\nraise RuntimeError('conteudo executado')\n",
        encoding="utf-8",
    )
    with pytest.raises(DefinitionError, match="ferramentas"):
        parse_agent_definition(caminho.read_text(encoding="utf-8"), caminho.name)


def test_versao_invalida_e_recusada() -> None:
    conteudo = CONTEUDO_VALIDO.replace("versao: 1", "versao: zero")
    with pytest.raises(DefinitionError, match="versao"):
        parse_agent_definition(conteudo, "teste.md")


def test_id_duplicado_e_recusado(tmp_path: Path) -> None:
    (tmp_path / "primeiro.md").write_text(CONTEUDO_VALIDO, encoding="utf-8")
    (tmp_path / "segundo.md").write_text(CONTEUDO_VALIDO, encoding="utf-8")
    with pytest.raises(DefinitionError, match="duplicado"):
        load_agent_definitions(tmp_path)


def test_conteudo_nao_confiavel_e_delimitado_antes_do_prompt() -> None:
    definicao = parse_agent_definition(CONTEUDO_VALIDO, "teste.md")
    prompt = render_prompt(definicao, {"codigo": "print(1)"})
    assert definicao.texto in prompt
    assert INICIO in prompt
    assert FIM in prompt
    assert "codigo:" in prompt


def test_marcadores_forjados_sao_recusados() -> None:
    definicao = parse_agent_definition(CONTEUDO_VALIDO, "teste.md")
    with pytest.raises(UntrustedContentError):
        render_prompt(definicao, {"codigo": INICIO})
