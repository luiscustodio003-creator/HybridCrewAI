"""Registo de prompts versionados e renderização segura."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from app.llm.egress import wrap_untrusted


class PromptError(ValueError):
    """Base para erros de carregamento de prompt."""


class PromptNotFound(PromptError):
    """Identificador de prompt inexistente."""


class InvalidPromptVersion(PromptError):
    """Versão inexistente ou inválida."""


@dataclass(frozen=True, slots=True)
class PromptRecord:
    """Prompt carregado com identidade e conteúdo íntegros."""

    prompt_id: str
    version: int
    content_sha256: str
    text: str


class PromptRegistry:
    """Carrega prompts Markdown locais como dados, nunca como código."""

    __slots__ = ("_base_dir",)

    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base_dir = Path(base_dir) if base_dir is not None else Path(__file__).parent
        if not self._base_dir.is_dir():
            raise PromptError(f"Pasta de prompts inexistente: {self._base_dir}")

    @staticmethod
    def _validar_versao(version: int) -> int:
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise InvalidPromptVersion(f"Versão inválida: {version!r}.")
        return version

    @staticmethod
    def _analisar(conteudo: str, caminho: Path) -> PromptRecord:
        linhas = conteudo.splitlines()
        if not linhas or linhas[0].strip() != "---":
            raise PromptError(f"Prompt sem cabeçalho de metadados: {caminho.name}")
        try:
            fim = linhas[1:].index("---") + 1
        except ValueError as erro:
            raise PromptError(
                f"Prompt com cabeçalho não terminado: {caminho.name}"
            ) from erro
        metadados: dict[str, str] = {}
        for linha in linhas[1:fim]:
            if ":" not in linha:
                raise PromptError(f"Metadado inválido em {caminho.name}: {linha!r}")
            chave, valor = linha.split(":", 1)
            metadados[chave.strip()] = valor.strip()
        prompt_id = metadados.get("id", "")
        if not prompt_id:
            raise PromptError(f"Prompt sem id em {caminho.name}")
        try:
            versao = int(metadados.get("version", ""))
        except ValueError as erro:
            raise PromptError(f"Prompt sem versão válida em {caminho.name}") from erro
        if versao < 1:
            raise PromptError(f"Prompt com versão menor que 1 em {caminho.name}")
        texto = "\n".join(linhas[fim + 1 :]).strip()
        if not texto:
            raise PromptError(f"Prompt sem conteúdo em {caminho.name}")
        return PromptRecord(
            prompt_id=prompt_id,
            version=versao,
            content_sha256=hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            text=texto,
        )

    def _carregar(self) -> list[PromptRecord]:
        registos: list[PromptRecord] = []
        vistos: set[tuple[str, int]] = set()
        for caminho in sorted(self._base_dir.glob("*.md")):
            registo = self._analisar(caminho.read_text(encoding="utf-8"), caminho)
            chave = (registo.prompt_id, registo.version)
            if chave in vistos:
                raise PromptError(f"Prompt duplicado: {registo.prompt_id} v{registo.version}")
            vistos.add(chave)
            registos.append(registo)
        return registos

    def get(self, prompt_id: str, version: int = 1) -> PromptRecord:
        """Devolve um prompt exacto ou falha explicitamente."""
        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise PromptNotFound("Identificador de prompt inválido.")
        versao = self._validar_versao(version)
        disponiveis = [item for item in self._carregar() if item.prompt_id == prompt_id]
        if not disponiveis:
            raise PromptNotFound(f"Prompt inexistente: {prompt_id!r}")
        for registo in disponiveis:
            if registo.version == versao:
                return registo
        versoes = ", ".join(str(item.version) for item in disponiveis)
        raise InvalidPromptVersion(
            f"Prompt {prompt_id!r} não tem a versão {versao}; versões: {versoes}"
        )

    def render(
        self,
        prompt_id: str,
        version: int = 1,
        untrusted: Mapping[str, str] | None = None,
    ) -> str:
        """Junta blocos não confiáveis apenas através do delimitador seguro."""
        base = self.get(prompt_id, version)
        partes = [base.text]
        if untrusted is None:
            return base.text
        if not isinstance(untrusted, Mapping):
            raise TypeError("untrusted tem de ser um mapping.")
        for nome, conteudo in untrusted.items():
            if not isinstance(nome, str) or not isinstance(conteudo, str):
                raise TypeError("Chaves e valores de untrusted têm de ser strings.")
            partes.append(f"{nome}:\n{wrap_untrusted(conteudo)}")
        return "\n\n".join(partes)
