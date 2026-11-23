"""Integração real da CLI HCW com eventos e SQLite."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from app.core.events import EventContext, JsonlSink, new_event

RAIZ = Path(__file__).resolve().parents[2]
LIMITE = 10


def test_ponto_de_entrada_declarado_e_executavel() -> None:
    """O comando hcw está declarado e tem launcher no ambiente virtual."""
    conteudo = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    assert 'hcw = "app.cli:main"' in conteudo
    launcher = RAIZ / ".venv" / "Scripts" / "hcw.cmd"
    assert launcher.exists(), "Falta o launcher .venv\\Scripts\\hcw.cmd."


def test_doctor_verifica_config_sqlite_e_redaccao(tmp_path: Path) -> None:
    """O doctor real devolve zero com verificações verdadeiras."""
    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli",
            "doctor",
            "--base-dir",
            str(tmp_path),
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=LIMITE,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "config OK" in resultado.stdout
    assert "sqlite OK" in resultado.stdout
    assert "redaction OK" in resultado.stdout


def test_logs_follow_mostra_evento_em_tempo_real(tmp_path: Path) -> None:
    """Um evento escrito depois do arranque aparece no seguidor."""
    caminho = tmp_path / "events.jsonl"
    contexto = EventContext(
        correlation_id="corr-cli-real",
        task_id="task-cli-real",
        agent="open-code",
        phase="1",
    )
    processo = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "app.cli",
            "logs",
            "--follow",
            "--path",
            str(caminho),
            "--task-id",
            contexto.task_id,
            "--limit",
            "1",
            "--timeout",
            str(LIMITE),
        ],
        cwd=RAIZ,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    time.sleep(1.0)
    JsonlSink(caminho).write(
        new_event(contexto, kind="cli.integration", message="evento em tempo real")
    )
    saida, erros = processo.communicate(timeout=LIMITE + 5)

    assert processo.returncode == 0, erros
    assert contexto.correlation_id in saida
    assert contexto.task_id in saida
    assert "evento em tempo real" in saida
