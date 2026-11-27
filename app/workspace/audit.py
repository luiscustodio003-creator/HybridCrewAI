"""Registo de auditoria das operações do workspace."""

from __future__ import annotations

import json
import re
import stat
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from app.core.events import Event, EventContext, EventLevel, new_event
from app.llm.egress import redact_text
from app.workspace.paths import WorkspacePathError, validate_workspace_path

_DIRETORIO = ".file-ops"
_NOME = "audit.jsonl"
_STAGING = "audit-staging"
_CHAVES = frozenset({"operation_id", "path", "sha256", "size", "count", "outcome"})
_ID_PADRAO = re.compile(r"^[0-9a-f]{32}$")
_HASH_PADRAO = re.compile(r"^[0-9a-f]{64}$")
_MIN_ASCII_IMPRIMIVEL = 32


class AuditError(RuntimeError):
    """Auditoria indisponível, inválida ou com registo demasiado grande."""


@dataclass(frozen=True)
class AuditLimits:
    """Limites aplicados ao caminho e ao tamanho do registo de auditoria."""

    max_chars: int
    max_audit_bytes: int


class AuditTrail:
    """Regista eventos de auditoria sem guardar conteúdo de ficheiros."""

    __slots__ = ("_caminho", "_limites", "_lock", "_raiz")

    def __init__(self, root: Path, *, limits: AuditLimits) -> None:
        """Prepara o registo dentro da raiz verificada do workspace."""
        self._validar_limites(limits)
        diretorio = validate_workspace_path(
            root, _DIRETORIO, max_chars=limits.max_chars
        )
        self._raiz = diretorio.parent
        self._caminho = diretorio / _NOME
        self._limites = limits
        self._lock = Lock()

    @property
    def path(self) -> Path:
        """Caminho do ficheiro de auditoria."""
        return self._caminho

    def record(
        self,
        context: EventContext,
        /,
        *,
        kind: str,
        message: str,
        data: Mapping[str, object] | None = None,
        level: EventLevel = EventLevel.INFO,
    ) -> Event:
        """Cria e grava um evento com metadados verificados e redigidos."""
        evento = new_event(
            context,
            kind=self._texto(kind),
            message=self._texto(message),
            level=level,
            data=self._limpar(data or {}),
        )
        self._gravar(evento)
        return evento

    def read(self) -> tuple[Event, ...]:
        """Devolve os eventos gravados, na ordem original."""
        caminho = self._destino()
        if not caminho.exists():
            return ()
        if caminho.stat().st_size > self._limites.max_audit_bytes:
            raise AuditError("O registo de auditoria excede o tamanho permitido.")
        eventos: list[Event] = []
        try:
            with caminho.open("r", encoding="utf-8") as ficheiro:
                for linha in ficheiro:
                    if linha.strip():
                        eventos.append(Event.from_dict(json.loads(linha)))
        except (OSError, ValueError, TypeError) as exc:
            raise AuditError("O registo de auditoria não pôde ser lido.") from exc
        return tuple(eventos)

    @staticmethod
    def _validar_limites(limits: AuditLimits) -> None:
        """Rejeita limites que não protegem o registo."""
        if limits.max_chars < 1 or limits.max_audit_bytes < 1:
            raise AuditError("Os limites da auditoria são inválidos.")

    def _destino(self) -> Path:
        """Valida o ficheiro de auditoria antes de o abrir."""
        try:
            return validate_workspace_path(
                self._raiz,
                f"{_DIRETORIO}/{_NOME}",
                max_chars=self._limites.max_chars,
            )
        except WorkspacePathError as exc:
            raise AuditError("O registo de auditoria sai do workspace.") from exc

    def _texto(self, valor: str) -> str:
        """Limpa, redige e limita um texto antes de o registar."""
        if not isinstance(valor, str) or not valor.strip():
            raise AuditError("Os campos de texto da auditoria são obrigatórios.")
        texto = redact_text(valor.strip())
        if any(ord(caracter) < _MIN_ASCII_IMPRIMIVEL for caracter in texto):
            raise AuditError("O texto da auditoria contém caracteres de controlo.")
        return texto[: self._limites.max_chars]

    def _limpar(self, dados: Mapping[str, object]) -> dict[str, object]:
        """Mantém apenas metadados permitidos, com tipos e tamanhos seguros."""
        limpos: dict[str, object] = {}
        for chave, valor in dados.items():
            if chave not in _CHAVES:
                continue
            if chave in {"size", "count"}:
                if isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0:
                    limpos[chave] = valor
                continue
            if not isinstance(valor, str):
                continue
            texto = self._texto(valor)
            if chave == "sha256" and not _HASH_PADRAO.fullmatch(texto):
                continue
            if chave == "operation_id" and not _ID_PADRAO.fullmatch(texto):
                continue
            limpos[chave] = texto
        return limpos

    def _gravar(self, evento: Event) -> None:
        """Substitui o registo por uma cópia completa e válida."""
        destino = self._destino()
        linha = json.dumps(
            evento.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        with self._lock:
            atual = b""
            if destino.exists():
                if not stat.S_ISREG(destino.stat().st_mode):
                    raise AuditError("O registo de auditoria não é um ficheiro normal.")
                atual = destino.read_bytes()
            tamanho = len(atual) + len(linha.encode("utf-8")) + 1
            if tamanho > self._limites.max_audit_bytes:
                raise AuditError("O registo de auditoria excede o tamanho permitido.")
            candidato = (
                f"{_DIRETORIO}/{_STAGING}/{uuid.uuid4().hex}.jsonl"
            )
            staging = validate_workspace_path(
                self._raiz, candidato, max_chars=self._limites.max_chars
            )
            try:
                staging.parent.mkdir(parents=True, exist_ok=True)
                with staging.open("xb") as ficheiro:
                    ficheiro.write(atual)
                    ficheiro.write(f"{linha}\n".encode())
                staging.replace(destino)
            except (OSError, WorkspacePathError) as exc:
                raise AuditError("O evento não pôde ser gravado.") from exc
            finally:
                if staging.exists():
                    staging.unlink(missing_ok=True)
