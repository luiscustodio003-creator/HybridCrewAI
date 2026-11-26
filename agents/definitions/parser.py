"""Definições de agentes em Markdown como dados validados."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CAMPOS_OBRIGATORIOS = ("id", "nome", "versao", "entrada", "saida", "ferramentas")


class DefinitionError(ValueError):
    """Definição de agente inválida."""


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Agente lido de um ficheiro Markdown, nunca executado."""

    agent_id: str
    nome: str
    versao: int
    entrada: str
    saida: str
    ferramentas: tuple[str, ...]
    texto: str


def _ler_metadados(linhas: list[str], origem: str) -> dict[str, str]:
    metadados: dict[str, str] = {}
    for numero, linha in enumerate(linhas, start=2):
        if ":" not in linha:
            raise DefinitionError(
                f"Metadado inválido em {origem!r} na linha {numero}: use 'chave: valor'."
            )
        chave, valor = linha.split(":", 1)
        chave = chave.strip()
        valor = valor.strip()
        if not chave or not valor:
            raise DefinitionError(
                f"Metadado vazio em {origem!r} na linha {numero}."
            )
        if chave in metadados:
            raise DefinitionError(f"Campo duplicado em {origem!r}: {chave}.")
        metadados[chave] = valor
    return metadados


def _validar_metadados(metadados: dict[str, str], origem: str) -> int:
    obrigatorios = set(CAMPOS_OBRIGATORIOS)
    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in metadados]
    if ausentes:
        raise DefinitionError(
            f"Definição {origem!r} sem campo obrigatório: {', '.join(ausentes)}."
        )
    extras = sorted(set(metadados) - obrigatorios)
    if extras:
        raise DefinitionError(
            f"Definição {origem!r} com campo desconhecido: {', '.join(extras)}."
        )
    valor = metadados["versao"]
    if not valor.isdigit() or int(valor) < 1:
        raise DefinitionError(
            f"Definição {origem!r} com versao inválida: {valor!r}; use um inteiro >= 1."
        )
    return int(valor)


def _validar_ferramentas(valor: str, origem: str) -> tuple[str, ...]:
    ferramentas = tuple(item.strip() for item in valor.split(","))
    if not ferramentas or any(not item for item in ferramentas):
        raise DefinitionError(
            f"Definição {origem!r} com ferramentas inválidas: {valor!r}."
        )
    return ferramentas


def parse_agent_definition(conteudo: str, origem: str = "definição") -> AgentDefinition:
    """Valida o cabeçalho e devolve a definição como dado imutável."""
    if not isinstance(conteudo, str):
        raise TypeError("conteudo tem de ser string.")
    linhas = conteudo.splitlines()
    if not linhas or linhas[0].strip() != "---":
        raise DefinitionError(f"Definição {origem!r} sem cabeçalho de metadados.")
    try:
        fim = linhas[1:].index("---") + 1
    except ValueError as erro:
        raise DefinitionError(
            f"Definição {origem!r} com cabeçalho não terminado."
        ) from erro
    metadados = _ler_metadados(linhas[1:fim], origem)
    versao = _validar_metadados(metadados, origem)
    ferramentas = _validar_ferramentas(metadados["ferramentas"], origem)
    texto = "\n".join(linhas[fim + 1 :]).strip()
    if not texto:
        raise DefinitionError(f"Definição {origem!r} sem instruções.")
    return AgentDefinition(
        agent_id=metadados["id"],
        nome=metadados["nome"],
        versao=versao,
        entrada=metadados["entrada"],
        saida=metadados["saida"],
        ferramentas=ferramentas,
        texto=texto,
    )


def load_agent_definitions(
    base_dir: str | Path | None = None,
) -> tuple[AgentDefinition, ...]:
    """Carrega todas as definições Markdown de uma pasta, sem executar nada."""
    pasta = Path(base_dir) if base_dir is not None else Path(__file__).parent
    if not pasta.is_dir():
        raise DefinitionError(f"Pasta de definições inexistente: {pasta}")
    definicoes: list[AgentDefinition] = []
    vistos: set[str] = set()
    for caminho in sorted(pasta.glob("*.md")):
        definicao = parse_agent_definition(
            caminho.read_text(encoding="utf-8"), caminho.name
        )
        if definicao.agent_id in vistos:
            raise DefinitionError(
                f"Definição duplicada em {pasta}: {definicao.agent_id!r}."
            )
        vistos.add(definicao.agent_id)
        definicoes.append(definicao)
    return tuple(definicoes)
