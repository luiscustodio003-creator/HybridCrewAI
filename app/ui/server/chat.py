"""Chat local com histórico persistido e ligação ao gateway de modelos."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Final, Literal

from app.core.tasks import utc_now
from app.llm import ModelRequest, ModelResponse, ProviderKind
from app.llm.egress import redact_text
from app.llm.prompts import PromptRegistry
from app.llm.providers import ModelProvider

PROMPT_ID: Final = "sistema"
PROMPT_VERSION: Final = 1
MODELO_LOCAL: Final = "fake-local"
TIMEOUT_S: Final = 5.0
TIPO_MENSAGEM = Literal["user", "assistant"]

_SQL_CRIAR = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    task_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""
_SQL_GUARDAR = """
INSERT INTO chat_messages (role, content, task_id, correlation_id, created_at)
VALUES (?, ?, ?, ?, ?)
"""


def _texto_obrigatorio(valor: str, nome: str) -> str:
    """Valida e normaliza um campo textual obrigatório."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"O campo {nome} é obrigatório.")
    return valor.strip()


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Mensagem imutável do histórico do chat."""

    role: TIPO_MENSAGEM
    content: str
    task_id: str
    correlation_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        """Valida os campos e normaliza o conteúdo."""
        if self.role not in {"user", "assistant"}:
            raise ValueError("role tem de ser 'user' ou 'assistant'.")
        object.__setattr__(self, "content", _texto_obrigatorio(self.content, "content"))
        object.__setattr__(self, "task_id", _texto_obrigatorio(self.task_id, "task_id"))
        object.__setattr__(
            self, "correlation_id", _texto_obrigatorio(self.correlation_id, "correlation_id")
        )


class ChatStore:
    """Armazena mensagens de chat num ficheiro SQLite real."""

    __slots__ = ("_path",)

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Caminho do ficheiro de base de dados."""
        return self._path

    def _connect(self) -> sqlite3.Connection:
        """Abre uma ligação com espera por bloqueios."""
        ligacao = sqlite3.connect(self._path, timeout=5)
        ligacao.row_factory = sqlite3.Row
        ligacao.execute("PRAGMA busy_timeout=5000")
        return ligacao

    def initialize(self) -> None:
        """Cria a pasta e a tabela de mensagens, se necessário."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as ligacao:
            with ligacao:
                ligacao.execute(_SQL_CRIAR)

    def save(self, mensagem: ChatMessage) -> None:
        """Grava uma mensagem no histórico."""
        valores = (
            mensagem.role,
            mensagem.content,
            mensagem.task_id,
            mensagem.correlation_id,
            mensagem.created_at.isoformat(),
        )
        with closing(self._connect()) as ligacao:
            with ligacao:
                ligacao.execute(_SQL_GUARDAR, valores)

    def list_messages(self, task_id: str | None = None) -> list[ChatMessage]:
        """Devolve o histórico por ordem de gravação, opcionalmente por tarefa."""
        consulta = "SELECT * FROM chat_messages"
        parametros: tuple[object, ...] = ()
        if task_id is not None:
            consulta += " WHERE task_id = ?"
            parametros = (_texto_obrigatorio(task_id, "task_id"),)
        consulta += " ORDER BY id"
        with closing(self._connect()) as ligacao:
            linhas = ligacao.execute(consulta, parametros).fetchall()
        return [self._mensagem(linha) for linha in linhas]

    @staticmethod
    def _mensagem(linha: sqlite3.Row) -> ChatMessage:
        """Reconstrói uma mensagem a partir de uma linha SQLite."""
        return ChatMessage(
            role=linha["role"],
            content=linha["content"],
            task_id=linha["task_id"],
            correlation_id=linha["correlation_id"],
            created_at=datetime.fromisoformat(linha["created_at"]),
        )


@dataclass(slots=True)
class LocalChatProvider:
    """Fornecedor local determinístico usado quando não há modelo configurado."""

    model: str = MODELO_LOCAL
    provider: ProviderKind = field(init=False, default=ProviderKind.FAKE)

    def __post_init__(self) -> None:
        """Valida o nome do modelo local."""
        self.model = _texto_obrigatorio(self.model, "model")

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Devolve uma resposta curta sem sair do processo."""
        return ModelResponse(
            provider=request.provider,
            model=request.model,
            text="Recebi a tua mensagem e registei o pedido no histórico local.",
            task_id=request.task_id,
            correlation_id=request.correlation_id,
            latency_ms=0.0,
        )


class ChatService:
    """Compõe o prompt, chama o gateway e persiste o histórico da conversa."""

    __slots__ = ("_model", "_provider", "_registry", "_store", "_timeout_s")

    def __init__(
        self,
        store: ChatStore,
        provider: ModelProvider | None = None,
        *,
        model: str = MODELO_LOCAL,
        timeout_s: float = TIMEOUT_S,
        base_dir: str | Path | None = None,
    ) -> None:
        self._store = store
        self._store.initialize()
        escolhido: ModelProvider
        if provider is None:
            escolhido = LocalChatProvider(model)
        else:
            escolhido = provider
        self._provider = escolhido
        self._registry = PromptRegistry(base_dir)
        self._model = _texto_obrigatorio(model, "model")
        if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
            raise ValueError("timeout_s tem de ser um número.")
        if timeout_s <= 0:
            raise ValueError("timeout_s tem de ser positivo.")
        self._timeout_s = float(timeout_s)

    @property
    def provider(self) -> ModelProvider:
        """Fornecedor usado nas chamadas ao gateway."""
        return self._provider

    @provider.setter
    def provider(self, valor: ModelProvider) -> None:
        """Substitui o fornecedor, por exemplo em testes de integração."""
        self._provider = valor

    @property
    def store(self) -> ChatStore:
        """Armazenamento do histórico do chat."""
        return self._store

    def enviar(
        self,
        mensagem: str,
        *,
        task_id: str,
        correlation_id: str,
    ) -> ChatMessage:
        """Envia uma mensagem ao gateway e grava o par de mensagens."""
        texto = _texto_obrigatorio(mensagem, "message")
        tarefa = _texto_obrigatorio(task_id, "task_id")
        correlacao = _texto_obrigatorio(correlation_id, "correlation_id")
        prompt = self._registry.render(
            PROMPT_ID,
            PROMPT_VERSION,
            {"mensagem do utilizador": redact_text(texto)},
        )
        pedido = ModelRequest(
            provider=self._provider.provider,
            model=self._model,
            prompt=prompt,
            timeout_s=self._timeout_s,
            task_id=tarefa,
            correlation_id=correlacao,
        )
        resposta = self._provider.complete(pedido)
        agora = utc_now()
        self._store.save(
            ChatMessage("user", texto, tarefa, correlacao, agora)
        )
        resposta_chat = ChatMessage(
            "assistant", resposta.text, tarefa, correlacao, agora
        )
        self._store.save(resposta_chat)
        return resposta_chat


def serializar_mensagem(mensagem: ChatMessage) -> dict[str, object]:
    """Converte uma mensagem num objecto JSON sem campos internos."""
    return {
        "role": mensagem.role,
        "content": mensagem.content,
        "task_id": mensagem.task_id,
        "correlation_id": mensagem.correlation_id,
        "created_at": mensagem.created_at.isoformat(),
    }
