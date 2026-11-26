"""Geração determinística do relatório final da Fase 4."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from tests.eval.cases import CASES
from tests.eval.scorer import ResultadoAvaliacao

TAREFAS: tuple[str, ...] = (
    "HCW-04-001 — identificados os fluxos e limites do MVP.",
    "HCW-04-002 — consolidado o contrato do caso dourado.",
    "HCW-04-003 — definidos os limites da guarda de subprocesso.",
    "HCW-04-004 — implementado o contrato de saída dos agentes.",
    "HCW-04-005 — implementada a validação de conteúdo não confiável.",
    "HCW-04-006 — implementado o emissor de tokens opacos.",
    "HCW-04-007 — implementada a interface local de aprovação.",
    "HCW-04-008 — executado o caso dourado da calculadora.",
    "HCW-04-009 — implementada a retoma verificável do fluxo CREATE.",
    "HCW-04-010 — concluída a interface local de equipa e aprovação.",
    "HCW-04-011 — executado o harness com cinco casos e pontuação.",
)

ACEITACAO: tuple[str, ...] = (
    "Cinco casos de referência são pontuados e o caso dourado é obrigatório.",
    "Pontuação mínima é 4 em 5 e o relatório final inclui comandos, resultados e digests.",
    "Relatório não contém segredos, token real ou prompt completo.",
)

LIMITACOES_FIXAS: tuple[str, ...] = (
    "O executor é não isolado; a guarda reduz ficheiros e rede, mas não é uma sandbox.",
    "Os fornecedores de modelo nos testes são determinísticos e locais (ProviderKind.FAKE).",
    "O relatório regista digests e estados curtos; nunca regista tokens nem prompts.",
)

TAMANHO_DIGEST = 64

CHAVES_EVIDENCIA: frozenset[str] = frozenset(
    {
        "diff_hash",
        "token_hash",
        "stdout_sha256",
        "relatorio_sha256",
        "digest_casos",
        "captura_equipa_sha256",
        "captura_aprovacao_sha256",
    }
)
PALAVRAS_PROIBIDAS: tuple[str, ...] = (
    "token",
    "prompt",
    "segredo",
    "senha",
    "chave privada",
)


def digest_relatorio(texto: str) -> str:
    """Devolve o SHA-256 do texto exacto do relatório."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _hex64(valor: str) -> bool:
    return (
        len(valor) == TAMANHO_DIGEST
        and valor == valor.lower()
        and all(caracter in "0123456789abcdef" for caracter in valor)
    )


def _texto_seguro(valor: object, limite: int) -> str | None:
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto or len(texto) > limite:
        return None
    if any(palavra in texto.lower() for palavra in PALAVRAS_PROIBIDAS):
        return None
    return texto.replace("|", "\\|")


def _nome_seguro(valor: str, limite: int) -> str:
    texto = valor.strip().replace("|", "\\|")
    return texto[:limite] if texto else ""


def _comandos_seguros(comandos: Sequence[object]) -> list[str]:
    return [
        texto for item in comandos if (texto := _texto_seguro(item, 220)) is not None
    ]


def _resultados_seguros(resultados: Mapping[str, object]) -> list[tuple[str, str]]:
    seguros: list[tuple[str, str]] = []
    for chave, valor in resultados.items():
        if any(palavra in chave.lower() for palavra in PALAVRAS_PROIBIDAS):
            continue
        texto = _texto_seguro(valor, 160)
        if texto is not None:
            seguros.append((chave.replace("|", "\\|"), texto))
    return seguros


def _evidencias_seguras(evidencias: Mapping[str, object]) -> list[tuple[str, str]]:
    return [
        (chave, valor)
        for chave, valor in evidencias.items()
        if chave in CHAVES_EVIDENCIA and isinstance(valor, str) and _hex64(valor)
    ]


def _linhas_casos(avaliacao: ResultadoAvaliacao) -> list[str]:
    linhas: list[str] = []
    for caso in CASES:
        resultado = next(
            (item for item in avaliacao.resultados if item.case_id == caso.id), None
        )
        estado = "PASSA" if resultado is not None and resultado.aprovado else "FALHA"
        obrigatorio = "sim" if caso.obrigatorio else "não"
        linhas.append(f"| {caso.id} | {caso.titulo} | {obrigatorio} | {estado} |")
    return linhas


def _linhas_verificacao(avaliacao: ResultadoAvaliacao) -> list[str]:
    linhas: list[str] = []
    for resultado in avaliacao.resultados:
        for verificacao in resultado.verificacoes:
            estado = "PASSA" if verificacao.passou else "FALHA"
            detalhe = _texto_seguro(verificacao.detalhe, 80) or "—"
            nome = _nome_seguro(verificacao.nome, 80) or resultado.case_id
            linhas.append(f"| {resultado.case_id} | {nome} | {estado} | {detalhe} |")
    return linhas


def renderizar_relatorio(
    avaliacao: ResultadoAvaliacao,
    *,
    comandos: Sequence[object] = (),
    resultados: Mapping[str, object] | None = None,
    evidencias: Mapping[str, object] | None = None,
    limitacoes: Sequence[object] = (),
) -> str:
    """Renderiza o relatório final com apenas valores curtos e verificáveis."""
    linhas_comandos = _comandos_seguros(comandos)
    linhas_resultados = _resultados_seguros(resultados or {})
    linhas_evidencias = _evidencias_seguras(evidencias or {})
    linhas_limitacoes = [
        texto
        for item in (*LIMITACOES_FIXAS, *limitacoes)
        if (texto := _texto_seguro(item, 220)) is not None
    ]
    linhas: list[str] = [
        "# Relatório final — Fase 04",
        "",
        "Data: 2026-11-26 · Gate: EM EXECUÇÃO · Depende de HCW-04-012.",
        "",
        "## O que foi feito (por tarefa)",
        "",
        *TAREFAS,
        "",
        "## Casos de referência",
        "",
        "| Caso | Descrição | Obrigatório | Estado |",
        "|---|---|---|---|",
        *_linhas_casos(avaliacao),
        "",
        f"Pontuação: {avaliacao.pontuacao}/{avaliacao.total} · "
        f"Mínimo: {avaliacao.minimo} · "
        f"Dourado: {'PASSA' if avaliacao.caso_dourado_presente else 'FALHA'} · "
        f"Resultado: {'APROVADO' if avaliacao.aprovado else 'NÃO APROVADO'}",
        "",
        "## Verificações",
        "",
        "| Caso | Verificação | Estado | Detalhe |",
        "|---|---|---|---|",
        *_linhas_verificacao(avaliacao),
        "",
        "## Comandos executados",
        "",
        *[f"{indice}. `{item}`" for indice, item in enumerate(linhas_comandos, 1)],
        "",
        "## Resultados (passam / falham / ignorados)",
        "",
        "| Verificação | Resultado |",
        "|---|---|",
        *[f"| {chave} | {valor} |" for chave, valor in linhas_resultados],
        "",
        "## Critérios de aceitação (um por linha, com a prova)",
        "",
        *[f"- [x] {item}" for item in ACEITACAO],
        "",
        "## Evidências",
        "",
        "| Nome | Digest/valor |",
        "|---|---|",
        *[f"| {chave} | `{valor}` |" for chave, valor in linhas_evidencias],
        "",
        "## Decisões tomadas (ADR e IDs)",
        "",
        "- ADR-004 — aprovação apenas por token opaco emitido pela UI local.",
        "- ADR-005 — saída do modelo tratada como dado não confiável.",
        "- ADR-006 — checkpoints com chaves de idempotência por passo.",
        "",
        "## Limitações conhecidas",
        "",
        *[f"- {item}" for item in linhas_limitacoes],
        "",
        "## Ideias adiadas (IDEA-xxx)",
        "",
        "- Nenhuma ideia registada nesta tarefa.",
        "",
        "## Como demonstrar (passos para um agente novo)",
        "",
        "1. Ler `tasks.yaml`, `STATE.md` e `docs/requirements.yaml`.",
        "2. Rodar `python -m pytest -q tests/eval/test_reference_cases.py`.",
        "3. Rodar o gate com `--deselect tests/ui/test_browser.py::test_evidencia_real_no_browser`.",
        "4. Comparar os digests acima com a saída dos testes.",
        "",
    ]
    return "\n".join(linhas)


def main(argv: Sequence[str] | None = None) -> int:
    """Lê a avaliação em JSON e escreve o relatório no destino escolhido."""
    parser = argparse.ArgumentParser(description="Gera o relatório final da Fase 4.")
    parser.add_argument("--avaliacao", required=True, type=Path)
    parser.add_argument("--metadados", type=Path)
    parser.add_argument("--comandos", nargs="*", default=[])
    parser.add_argument("--resultados", default="{}")
    parser.add_argument("--evidencias", default="{}")
    parser.add_argument("--limitacoes", nargs="*", default=[])
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args(argv)
    dados = cast(
        dict[str, object], json.loads(args.avaliacao.read_text(encoding="utf-8"))
    )
    metadados: dict[str, object] = (
        cast(dict[str, object], json.loads(args.metadados.read_text(encoding="utf-8")))
        if args.metadados is not None
        else {}
    )
    comandos = cast(Sequence[object], metadados.get("comandos", args.comandos))
    resultados = cast(
        dict[str, object],
        metadados.get("resultados", json.loads(args.resultados)),
    )
    evidencias = cast(
        dict[str, object],
        metadados.get("evidencias", json.loads(args.evidencias)),
    )
    limitacoes = cast(Sequence[object], metadados.get("limitacoes", args.limitacoes))
    avaliacao = ResultadoAvaliacao.de_dict(dados)
    texto = renderizar_relatorio(
        avaliacao,
        comandos=comandos,
        resultados=resultados,
        evidencias=evidencias,
        limitacoes=limitacoes,
    )
    if args.saida is not None:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(texto, encoding="utf-8")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
