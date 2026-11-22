"""Testes da escada de modelos e da matriz de fallback."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.llm import ProviderKind
from app.llm.router import (
    LadderError,
    StepAction,
    TaskKind,
    load_ladder,
    plan_fallback,
)


def _escrever_config(diretorio: Path, nome: str, dados: dict[str, object]) -> Path:
    caminho = diretorio / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return caminho


def _config(*, com_ollama: bool = True) -> dict[str, object]:
    leve: list[dict[str, str]] = [
        {"provider": "gemini-text", "model": "gemini-rapido"},
        {"provider": "gemini-live", "model": "gemini-voz"},
    ]
    codigo: list[dict[str, str]] = [
        {"provider": "gemini-text", "model": "gemini-forte"},
        {"provider": "external", "model": "outro-cloud"},
    ]
    if com_ollama:
        leve.append({"provider": "ollama", "model": "ollama-leve"})
        codigo.append({"provider": "ollama", "model": "ollama-codigo"})
    return {
        "version": 1,
        "ladders": {"light": leve, "code": codigo},
    }


def test_gemini_para_gemini_e_automatico_e_outro_cloud_exige_autorizacao(
    tmp_path: Path,
) -> None:
    caminho = _escrever_config(tmp_path, "escada.json", _config())
    decisoes = plan_fallback(
        load_ladder(caminho),
        TaskKind.CODE,
        source_provider=ProviderKind.GEMINI_TEXT,
    )
    assert decisoes[0].action is StepAction.USE
    assert "automático" in decisoes[0].reason
    assert decisoes[1].action is StepAction.REQUIRE_AUTHORIZATION
    assert "autorização explícita" in decisoes[1].reason
    autorizadas = plan_fallback(
        load_ladder(caminho),
        TaskKind.CODE,
        source_provider=ProviderKind.GEMINI_TEXT,
        external_cloud_authorized=True,
    )
    assert autorizadas[1].action is StepAction.USE


def test_gemini_para_ollama_so_em_tarefas_leves_e_codigo_pausa(tmp_path: Path) -> None:
    caminho = _escrever_config(tmp_path, "escada.json", _config())
    escada = load_ladder(caminho)
    leve = plan_fallback(escada, TaskKind.LIGHT, source_provider=ProviderKind.GEMINI_LIVE)
    codigo = plan_fallback(escada, TaskKind.CODE, source_provider=ProviderKind.GEMINI_LIVE)
    assert leve[-1].action is StepAction.USE
    assert "tarefa leve" in leve[-1].reason
    assert codigo[-1].action is StepAction.PAUSE
    assert "decisão" in codigo[-1].reason


def test_escada_vem_de_ficheiro_e_remover_modelo_nao_muda_codigo(tmp_path: Path) -> None:
    completo = _escrever_config(tmp_path, "completo.json", _config())
    reduzido = _escrever_config(
        tmp_path,
        "reduzido.json",
        _config(com_ollama=False),
    )
    assert load_ladder(completo).models(TaskKind.LIGHT) == (
        "gemini-rapido",
        "gemini-voz",
        "ollama-leve",
    )
    assert load_ladder(reduzido).models(TaskKind.LIGHT) == ("gemini-rapido", "gemini-voz")
    invalido = _escrever_config(
        tmp_path,
        "invalido.json",
        {"version": 99, "ladders": _config()["ladders"]},
    )
    with pytest.raises(LadderError, match="version"):
        load_ladder(invalido)
