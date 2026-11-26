"""Emissão e validação de tokens de aprovação da interface local."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from app.core.local_auth import origem_valida, pedido_autorizado
from approvals.tokens.models import (
    VALIDADE_MINUTOS,
    ApprovalDenied,
    ApprovalToken,
    DadosInvalidos,
    DiffAlterado,
    SolicitacaoAprovacao,
    TarefaInvalida,
    TokenExpirado,
    TokenInvalido,
    agora_utc,
    hash_diff_obrigatorio,
    texto_obrigatorio,
)

if TYPE_CHECKING:
    from app.core.config import Settings
    from approvals.tokens.models import Clock as TokenClock


@dataclass(frozen=True, slots=True)
class _Registro:
    """Registo interno com o valor opaco protegido por digest."""

    token: ApprovalToken
    digest: str = field(repr=False)


def _digest(valor: str) -> str:
    """Produz o digest usado como chave sem guardar o token em claro."""
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()


class TokenStore:
    """Armazém em memória de tokens emitidos apenas pela interface autenticada."""

    def __init__(
        self,
        settings: Settings,
        relogio: TokenClock | None = None,
    ) -> None:
        """Configura o emissor com o relógio injectado para testes determinísticos."""
        self._settings = settings
        self._relogio: TokenClock = relogio or agora_utc
        self._tokens: dict[str, _Registro] = {}

    @property
    def quantidade(self) -> int:
        """Devolve o número de tokens actualmente registados."""
        return len(self._tokens)

    def emitir(self, solicitacao: SolicitacaoAprovacao) -> ApprovalToken:
        """Emite um token quando o pedido vem da interface local autenticada."""
        if not isinstance(solicitacao, SolicitacaoAprovacao):
            raise DadosInvalidos("O pedido tem de ser uma SolicitacaoAprovacao.")
        origem = solicitacao.cabecalhos.get("Origin")
        sec_fetch_site = solicitacao.cabecalhos.get("Sec-Fetch-Site")
        if not origem_valida(
            origem, solicitacao.porta, sec_fetch_site
        ) or not pedido_autorizado(dict(solicitacao.cabecalhos), self._settings):
            raise ApprovalDenied(
                "A aprovação só pode ser emitida pelo servidor da UI autorizado."
            )
        task_id = texto_obrigatorio(solicitacao.task_id, "task_id")
        correlation_id = texto_obrigatorio(solicitacao.correlation_id, "correlation_id")
        diff_hash = hash_diff_obrigatorio(solicitacao.diff_hash)
        emitido_em = self._relogio()
        if emitido_em.tzinfo is None:
            raise DadosInvalidos("O relógio da aprovação tem de devolver UTC.")
        valor = secrets.token_urlsafe(32)
        token = ApprovalToken(
            token=valor,
            task_id=task_id,
            correlation_id=correlation_id,
            diff_hash=diff_hash,
            emitido_em=emitido_em,
            expira_em=emitido_em + timedelta(minutes=VALIDADE_MINUTOS),
        )
        digest = _digest(valor)
        self._tokens[digest] = _Registro(token=token, digest=digest)
        return token

    def validar(self, valor: str, task_id: str, diff_hash: str) -> ApprovalToken:
        """Valida o token apresentado contra tarefa, diff e prazo de validade."""
        if not isinstance(valor, str) or not valor:
            raise TokenInvalido("Token de aprovação desconhecido.")
        registro = self._tokens.get(_digest(valor))
        if registro is None:
            raise TokenInvalido("Token de aprovação desconhecido.")
        if not hmac.compare_digest(registro.token.task_id, task_id):
            raise TarefaInvalida(
                "O token de aprovação não corresponde à tarefa apresentada."
            )
        if not hmac.compare_digest(registro.token.diff_hash, diff_hash):
            raise DiffAlterado(
                "O diff mudou desde a aprovação; peça uma nova aprovação na UI."
            )
        if self._relogio() >= registro.token.expira_em:
            raise TokenExpirado("O token expirou; peça uma nova aprovação na UI.")
        return registro.token
