"""Execução determinística dos casos de referência e serialização segura."""

from __future__ import annotations

import argparse
import json
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pytest
from tests.eval.cases import CASES
from tests.eval.scorer import CaseResult, executar_caso, pontuar


def executar_todos() -> tuple[CaseResult, ...]:
    """Executa os cinco casos isolados e devolve os resultados na ordem estável."""
    resultados: list[CaseResult] = []
    with tempfile.TemporaryDirectory(
        prefix="hcw-04-011-", ignore_cleanup_errors=True
    ) as temporario:
        for indice, caso in enumerate(CASES):
            destino = Path(temporario) / f"caso-{indice}"
            destino.mkdir()
            patches = pytest.MonkeyPatch()
            try:
                resultados.append(executar_caso(caso, destino, patches))
            finally:
                patches.undo()
    return tuple(resultados)


def main(argv: Sequence[str] | None = None) -> int:
    """Escreve a avaliação em JSON com comentários e digests, sem segredos."""
    parser = argparse.ArgumentParser(description="Executa o harness de avaliação.")
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args(argv)
    avaliacao = pontuar(executar_todos())
    conteudo = json.dumps(
        avaliacao.para_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    if args.saida is None:
        print(conteudo)
    else:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(conteudo + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
