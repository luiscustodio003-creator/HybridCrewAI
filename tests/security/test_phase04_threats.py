"""Consolidação de segurança e documentação da Fase 4."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from approvals.tokens import SolicitacaoAprovacao, TokenStore
from execution import ExecutionRequest, SimpleRunner

from app.core.config import load_settings
from app.core.results import ToolStatus

if TYPE_CHECKING:
    from app.core.config import Settings

RAIZ = Path(__file__).resolve().parents[2]
MODELO_AMEACAS = RAIZ / "THREAT_MODEL.md"
RELATORIO_SEGURANCA = RAIZ / "docs" / "reports" / "phase-04-security.md"
RELATORIO_FINAL = RAIZ / "docs" / "reports" / "phase-04.md"
RELATORIO_TAREFA = RAIZ / "reports" / "tasks" / "HCW-04-012.md"
DOCUMENTACAO_EXECUTOR = RAIZ / "execution" / "README.txt"
PROMPT_SISTEMA = RAIZ / "app" / "llm" / "prompts" / "system.md"
HASH_DIFUSAO = "a" * 64
TOKEN_FALSO = "token-falso-com-16"
PORTA = 8765
COLUNAS_MODELO = 4
TAMANHO_MINIMO_PROMPT = 40


def _settings(tmp_path: Path) -> Settings:
    """Carrega configuração isolada com token falso de teste."""
    base = tmp_path / "project"
    base.mkdir()
    return load_settings(
        {"HCW_UI_ENABLED": "true", "HCW_UI_TOKEN": TOKEN_FALSO},
        base_dir=base,
    )


def _token(store: TokenStore, *, task_id: str, correlation_id: str) -> str:
    """Emite token autenticado para a tarefa indicada."""
    return store.emitir(
        SolicitacaoAprovacao(
            task_id=task_id,
            correlation_id=correlation_id,
            diff_hash=HASH_DIFUSAO,
            headers={
                "Authorization": f"Bearer {TOKEN_FALSO}",
                "Origin": f"http://127.0.0.1:{PORTA}",
            },
            porta=PORTA,
        )
    ).token


def test_modelo_de_ameacas_da_fase_4_liga_ameacas_a_testes_reais() -> None:
    """Toda a ameaça da Fase 4 tem teste real e resultado PASSA."""
    linhas = MODELO_AMEACAS.read_text(encoding="utf-8").splitlines()
    ameacas: list[str] = []
    for linha in linhas:
        if not linha.startswith("|"):
            continue
        colunas = [coluna.strip() for coluna in linha.strip("|").split("|")]
        if len(colunas) != COLUNAS_MODELO or "4" not in colunas[1].replace(
            " ", ""
        ).split(","):
            continue
        ameacas.append(colunas[0])
        assert "tests/" in colunas[3], colunas[0]
        assert "test_" in colunas[3], colunas[0]
        assert "PASSA" in colunas[3], colunas[0]
    assert ameacas, "nenhuma ameaça da Fase 4 encontrada"


def test_executor_nao_isolado_recusa_sem_token_valido(tmp_path: Path) -> None:
    """Sem token válido não há subprocesso e o resultado não é isolado."""
    settings = _settings(tmp_path)
    runner = SimpleRunner(settings, TokenStore(settings))
    resultado = runner.executar(
        ExecutionRequest(
            task_id="tarefa-sem-token",
            correlation_id="correlacao-sem-token",
            diff_hash=HASH_DIFUSAO,
            approval_token="token-invalido",
            command=(sys.executable, "-c", "print('nao-deve-executar')"),
            timeout_s=10,
        )
    )

    assert resultado.isolated is False
    assert resultado.tool_result.status is ToolStatus.FAILED
    assert resultado.stdout == ""
    assert resultado.stderr == ""
    assert "aprovação recusada" in (resultado.error or "")


def test_documentacao_declara_executor_nao_isolado() -> None:
    """A limitação do executor fica explícita no código e na documentação."""
    documentacao = DOCUMENTACAO_EXECUTOR.read_text(encoding="utf-8").lower()
    assert "não isolado" in documentacao
    assert "isolated=false" in documentacao
    assert "isolamento forte" in documentacao


def test_relatorios_da_fase_4_nao_expoem_segredos_nem_prompt() -> None:
    """Relatórios e modelo de ameaças não contêm segredos nem prompt completo."""
    prompt = PROMPT_SISTEMA.read_text(encoding="utf-8").strip()
    assert len(prompt) > TAMANHO_MINIMO_PROMPT
    for caminho in (
        RELATORIO_SEGURANCA,
        RELATORIO_FINAL,
        RELATORIO_TAREFA,
        MODELO_AMEACAS,
    ):
        conteudo = caminho.read_text(encoding="utf-8")
        assert TOKEN_FALSO not in conteudo, caminho.name
        assert f"Bearer {TOKEN_FALSO}" not in conteudo, caminho.name
        assert "sk-" not in conteudo, caminho.name
        assert "-----BEGIN" not in conteudo, caminho.name
        assert prompt not in conteudo, caminho.name


def test_relatorio_de_seguranca_regista_evidencia_real() -> None:
    """O relatório de segurança cita comandos, testes e limitações executadas."""
    texto = RELATORIO_SEGURANCA.read_text(encoding="utf-8")
    assert "Comandos executados" in texto
    assert "tests/security/test_phase04_threats.py" in texto
    assert "python -m pytest -q tests/security/test_phase04_threats.py" in texto
    assert "não isolado" in texto.lower()
    assert "Limitações conhecidas" in texto
