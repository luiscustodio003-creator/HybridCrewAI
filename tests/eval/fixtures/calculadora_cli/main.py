"""Calculadora de linha de comandos usada no caso dourado."""

from __future__ import annotations

import argparse


def somar(a: int, b: int) -> int:
    """Devolve a soma de dois inteiros."""
    return a + b


def subtrair(a: int, b: int) -> int:
    """Devolve a subtração de dois inteiros."""
    return a - b


def construir_parser() -> argparse.ArgumentParser:
    """Constrói o parser das operações suportadas."""
    parser = argparse.ArgumentParser(description="Calculadora de linha de comandos.")
    operacoes = parser.add_subparsers(dest="operacao", required=True)
    for nome in ("somar", "subtrair"):
        item = operacoes.add_parser(nome)
        item.add_argument("a", type=int)
        item.add_argument("b", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa a operação pedida e escreve o resultado."""
    argumentos = construir_parser().parse_args(argv)
    operacoes = {"somar": somar, "subtrair": subtrair}
    print(operacoes[argumentos.operacao](argumentos.a, argumentos.b))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
