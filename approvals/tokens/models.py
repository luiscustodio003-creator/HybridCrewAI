"""Modelos imutáveis dos tokens de aprovação da interface local."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final

VALIDADE_MINUTOS: Final = 15
MAX_ID_CHARS: Final = 120
HASH_DIFUSAO: Final = 64
_PADRAO_HASH = re.compile(rf"[0-9a-f]{{{HASH_DIFUSAO}}}")

Clock = Callable[[], datetime]


class ApprovalError(Exception):
    """Falha de aprovação com acção sugerida para quem a recebe."""


class ApprovalDenied(ApprovalError):
    """Pedido sem origem e autenticação do servidor da interface."""


class DadosInvalidos(ApprovalError):
    """Dados da aprovação fora do contrato esperado."""


class TokenInvalido(ApprovalError):
    """Token desconhecido ou impossível de validar."""


class TokenExpirado(ApprovalError):
    """Token válido apenas fora do prazo permitido."""


class TarefaInvalida(ApprovalError):
    """Token apresentado para uma tarefa diferente da aprovada."""


class DiffAlterado(ApprovalError):
    """Diff apresentado depois da emissão do token."""


def agora_utc() -> datetime:
    """Devolve a hora actual em UTC para cálculo de expiração."""
    return datetime.now(UTC)


def texto_obrigatorio(valor: object, nome: str) -> str:
    """Valida um identificador curto e não vazio."""
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidos(f"O campo {nome} é obrigatório e não pode estar vazio.")
    texto = valor.strip()
    if len(texto) > MAX_ID_CHARS:
        raise DadosInvalidos(f"O campo {nome} excede o tamanho permitido.")
    return texto


def hash_diff_obrigatorio(valor: object) -> str:
    """Valida o hash SHA-256 do diff em minúsculas hexadecimais."""
    if not isinstance(valor, str) or _PADRAO_HASH.fullmatch(valor) is None:
        raise DadosInvalidos(
            "O campo diff_hash tem de ser SHA-256 hexadecimal com 64 caracteres."
        )
    return valor


def calcular_hash_diff(snapshot_hash: object, alteracao_hash: object) -> str:
    """Calcula o hash canónico que liga o snapshot verificado à alteração."""
    origem = hash_diff_obrigatorio(snapshot_hash)
    destino = hash_diff_obrigatorio(alteracao_hash)
    serializado = json.dumps(
        {"snapshot_hash": origem, "alteracao_hash": destino},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SolicitacaoAprovacao:
    """Pedido de token feito pelo servidor local com cabeçalhos autenticados."""

    task_id: str
    correlation_id: str
    diff_hash: str
    headers: Mapping[str, str]
    porta: int
    cabecalhos: Mapping[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Copia os cabeçalhos para impedir alteração depois da validação."""
        if not isinstance(self.headers, Mapping):
            raise DadosInvalidos("Os cabeçalhos da aprovação têm de ser um mapping.")
        copia = {str(chave): str(valor) for chave, valor in self.headers.items()}
        object.__setattr__(self, "cabecalhos", copia)
        if isinstance(self.porta, bool) or not isinstance(self.porta, int):
            raise DadosInvalidos("A porta da interface tem de ser um inteiro.")


@dataclass(frozen=True, slots=True)
class ApprovalToken:
    """Token opaco ligado a tarefa, correlação, diff e prazo de validade."""

    token: str = field(repr=False)
    task_id: str
    correlation_id: str
    diff_hash: str
    emitido_em: datetime
    expira_em: datetime

    def __post_init__(self) -> None:
        """Valida os dados expostos pelo token sem revelar o valor secreto."""
        if not isinstance(self.token, str) or not self.token:
            raise DadosInvalidos("O token não pode estar vazio.")
        for nome in ("task_id", "correlation_id"):
            texto_obrigatorio(getattr(self, nome), nome)
        hash_diff_obrigatorio(self.diff_hash)
        if self.emitido_em.tzinfo is None or self.expira_em.tzinfo is None:
            raise DadosInvalidos("As datas do token têm de incluir fuso horário.")
        if self.expira_em <= self.emitido_em:
            raise DadosInvalidos("A expiração tem de ser posterior à emissão.")
