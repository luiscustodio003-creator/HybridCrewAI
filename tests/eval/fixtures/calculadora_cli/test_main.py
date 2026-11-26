"""Testes da calculadora de linha de comandos do caso dourado."""

import pytest
from main import main, somar, subtrair

SOMA_ESPERADA = 5
DIFERENCA_ESPERADA = 3


def test_somar() -> None:
    """Confirma a soma de dois inteiros."""
    assert somar(2, 3) == SOMA_ESPERADA


def test_subtrair() -> None:
    """Confirma a subtração de dois inteiros."""
    assert subtrair(7, 4) == DIFERENCA_ESPERADA


def test_cli_somar(capsys: pytest.CaptureFixture[str]) -> None:
    """Confirma a operação somar pela interface de linha de comandos."""
    assert main(["somar", "2", "3"]) == 0
    assert capsys.readouterr().out.strip() == "5"


def test_cli_subtrair(capsys: pytest.CaptureFixture[str]) -> None:
    """Confirma a operação subtrair pela interface de linha de comandos."""
    assert main(["subtrair", "7", "4"]) == 0
    assert capsys.readouterr().out.strip() == "3"
