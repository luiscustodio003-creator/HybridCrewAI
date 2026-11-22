"""Ponto de entrada da interface de linha de comando do HybridCrewAI."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.cli.doctor import run as executar_doctor
from app.cli.logs import follow


def _criar_parser() -> argparse.ArgumentParser:
    """Constrói a gramática explícita e segura de comandos da CLI."""
    parser = argparse.ArgumentParser(
        prog="hcw",
        description="Ferramentas locais do HybridCrewAI.",
    )
    comandos = parser.add_subparsers(dest="comando", required=True)

    logs = comandos.add_parser("logs", help="Mostra eventos do registo JSONL.")
    logs.add_argument("--follow", action="store_true", required=True)
    logs.add_argument("--path", type=Path, required=True)
    logs.add_argument("--task-id")
    logs.add_argument("--limit", type=int, default=1)
    logs.add_argument("--timeout", type=float, default=10.0)

    doctor = comandos.add_parser("doctor", help="Verifica a instalação local.")
    doctor.add_argument("--base-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa o comando pedido e devolve o código de saída."""
    argumentos = _criar_parser().parse_args(argv)
    if argumentos.comando == "logs":
        return follow(
            argumentos.path,
            task_id=argumentos.task_id,
            limit=argumentos.limit,
            timeout=argumentos.timeout,
        )
    return executar_doctor(argumentos.base_dir)
