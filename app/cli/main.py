"""Ponto de entrada da interface de linha de comando do HybridCrewAI."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.cli.doctor import run as executar_doctor
from app.cli.llm_ping import ParametrosPing
from app.cli.llm_ping import run as executar_llm_ping
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

    llm = comandos.add_parser("llm", help="Comandos do gateway de modelos.")
    llm_comandos = llm.add_subparsers(dest="llm_comando", required=True)
    ping = llm_comandos.add_parser("ping", help="Testa um fornecedor sem expor segredos.")
    ping.add_argument(
        "--provider",
        choices=("simulado", "ollama", "gemini"),
        default="simulado",
    )
    ping.add_argument("--endpoint")
    ping.add_argument("--model", default="hcw-ping")
    ping.add_argument("--prompt", default="ping")
    ping.add_argument("--timeout", type=float, default=5.0)
    ping.add_argument("--allow-cloud", action="store_true")
    ping.add_argument("--base-dir", type=Path)
    ping.add_argument("--api-key-env", default="GEMINI_API_KEY")
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
    if argumentos.comando == "llm":
        return executar_llm_ping(
            ParametrosPing(
                provider=argumentos.provider,
                endpoint=argumentos.endpoint,
                model=argumentos.model,
                prompt=argumentos.prompt,
                timeout_s=argumentos.timeout,
                allow_cloud=argumentos.allow_cloud,
                base_dir=argumentos.base_dir,
                api_key_env=argumentos.api_key_env,
            )
        )
    return executar_doctor(argumentos.base_dir)
