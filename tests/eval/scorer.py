"""Modelos, auxiliares e pontuação dos casos de referência da Fase 4."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from approvals.tokens import SolicitacaoAprovacao, TokenStore
from tests.integration.test_create_workflow_checkpoint import (
    CHAVES,
    CORRELATION_ID,
    DIFF_HASH,
    TASK_ID,
    TOKEN_FALSO,
)
from workflows.create import PASSOS, CreateRequest

CASO_DOURADO_ID = "golden_calculadora"
PORTA = 8765
TIMEOUT_S = 5.0
PASSOS_ATE_APROVACAO = PASSOS[1:4]
PASSOS_APOS_APROVACAO = PASSOS[5:]
MINIMO_APROVACAO = 4
TAMANHO_DIGEST = 64
INDICE_TOKEN_HASH = 3
PASSOS_RESTANTES = 3
TOTAL_CASOS = 5
LIMITE_INFERIOR = 3


@dataclass(frozen=True, slots=True)
class Verificacao:
    """Uma verificação atómica com detalhe curto e não sensível."""

    nome: str
    passou: bool
    detalhe: str = ""


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Resultado de um caso de referência, sem prompts nem tokens."""

    case_id: str
    verificacoes: tuple[Verificacao, ...]
    evidencias: tuple[str, ...] = ()

    @property
    def aprovado(self) -> bool:
        """Indica se todas as verificações do caso passaram."""
        return bool(self.verificacoes) and all(
            item.passou for item in self.verificacoes
        )

    def para_dict(self) -> dict[str, object]:
        """Serializa o resultado para o gerador de relatório."""
        return {
            "case_id": self.case_id,
            "verificacoes": [
                {"nome": item.nome, "passou": item.passou, "detalhe": item.detalhe}
                for item in self.verificacoes
            ],
            "evidencias": list(self.evidencias),
        }

    @classmethod
    def de_dict(cls, dados: dict[str, object]) -> CaseResult:
        """Reconstrói um resultado a partir da serialização."""
        itens = cast(list[dict[str, object]], dados["verificacoes"])
        verificacoes = tuple(
            Verificacao(
                str(item["nome"]),
                bool(item["passou"]),
                str(item.get("detalhe", "")),
            )
            for item in itens
        )
        return cls(
            str(dados["case_id"]),
            verificacoes,
            tuple(str(item) for item in cast(list[object], dados["evidencias"])),
        )


@dataclass(frozen=True, slots=True)
class Case:
    """Caso de referência executável com identificador estável."""

    id: str
    titulo: str
    obrigatorio: bool
    executar: Callable[[Path, pytest.MonkeyPatch], CaseResult]


@dataclass(frozen=True, slots=True)
class ResultadoAvaliacao:
    """Conjunto fechado de casos com regra de aprovação explícita."""

    resultados: tuple[CaseResult, ...]
    minimo: int = MINIMO_APROVACAO

    def __post_init__(self) -> None:
        """Valida identificadores únicos e intervalo da pontuação mínima."""
        identificadores = [item.case_id for item in self.resultados]
        if len(identificadores) != len(set(identificadores)):
            raise ValueError("Identificadores de casos repetidos.")
        if not 1 <= self.minimo <= len(self.resultados):
            raise ValueError("Pontuação mínima fora do intervalo dos casos.")

    @property
    def pontuacao(self) -> int:
        """Devolve o número de casos aprovados."""
        return sum(1 for item in self.resultados if item.aprovado)

    @property
    def total(self) -> int:
        """Devolve o número total de casos."""
        return len(self.resultados)

    @property
    def caso_dourado(self) -> CaseResult | None:
        """Devolve o caso obrigatório quando presente."""
        return next(
            (item for item in self.resultados if item.case_id == CASO_DOURADO_ID),
            None,
        )

    @property
    def caso_dourado_presente(self) -> bool:
        """Indica se o caso dourado está no conjunto avaliado."""
        return self.caso_dourado is not None

    @property
    def aprovado(self) -> bool:
        """Exige caso dourado aprovado e pontuação mínima."""
        dourado = self.caso_dourado
        return (
            dourado is not None and dourado.aprovado and self.pontuacao >= self.minimo
        )

    def para_dict(self) -> dict[str, object]:
        """Serializa a avaliação para o gerador de relatório."""
        return {
            "minimo": self.minimo,
            "resultados": [item.para_dict() for item in self.resultados],
        }

    @classmethod
    def de_dict(cls, dados: dict[str, object]) -> ResultadoAvaliacao:
        """Reconstrói a avaliação a partir do JSON de entrada."""
        itens = cast(list[dict[str, object]], dados["resultados"])
        minimo = dados.get("minimo", MINIMO_APROVACAO)
        valor_minimo = minimo if isinstance(minimo, int) else int(str(minimo))
        return cls(
            tuple(CaseResult.de_dict(item) for item in itens),
            valor_minimo,
        )


def _checar(nome: str, condicao: bool, falha: str = "") -> Verificacao:
    return Verificacao(nome, condicao, "" if condicao else falha)


def executar_caso(
    caso: Case, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> CaseResult:
    """Executa um caso e converte falhas inesperadas em verificação curta."""
    try:
        return caso.executar(tmp_path, monkeypatch)
    except Exception as erro:
        return CaseResult(caso.id, (_checar("execução", False, type(erro).__name__),))


def _recusado(funcao: Callable[[], object], tipo: type[Exception]) -> bool:
    try:
        funcao()
    except tipo:
        return True
    except Exception:
        return False
    return False


def _token_de_outra_tarefa(tokens: TokenStore) -> str:
    return tokens.emitir(
        SolicitacaoAprovacao(
            task_id="outra-tarefa",
            correlation_id="corr-outra-tarefa",
            diff_hash=DIFF_HASH,
            porta=PORTA,
            headers={
                "Origin": f"http://127.0.0.1:{PORTA}",
                "Authorization": f"Bearer {TOKEN_FALSO}",
                "Sec-Fetch-Site": "same-origin",
            },
        )
    ).token


def _diff_alterado(token: str) -> CreateRequest:
    return CreateRequest(
        task_id=TASK_ID,
        correlation_id=CORRELATION_ID,
        pedido="Pedido com diff alterado.",
        diff_hash="c" * TAMANHO_DIGEST,
        token_aprovacao=token,
        chaves=CHAVES,
    )


def pontuar(
    resultados: Sequence[CaseResult], minimo: int = MINIMO_APROVACAO
) -> ResultadoAvaliacao:
    """Cria uma avaliação imutável a partir dos resultados dos casos."""
    return ResultadoAvaliacao(tuple(resultados), minimo)


def digest_casos(avaliacao: ResultadoAvaliacao) -> str:
    """Produz o digest canónico dos casos e verificações, sem detalhes livres."""
    dados = {
        "minimo": avaliacao.minimo,
        "pontuacao": avaliacao.pontuacao,
        "total": avaliacao.total,
        "casos": [
            {
                "case_id": item.case_id,
                "aprovado": item.aprovado,
                "verificacoes": [
                    {"nome": ver.nome, "passou": ver.passou}
                    for ver in item.verificacoes
                ],
                "evidencias": [
                    evidencia.split("=", 1)[0] for evidencia in item.evidencias
                ],
            }
            for item in avaliacao.resultados
        ],
    }
    bruto = json.dumps(dados, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()
