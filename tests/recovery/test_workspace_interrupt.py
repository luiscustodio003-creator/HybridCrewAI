"""Recuperação de escritas interrompidas no workspace."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import cast

import pytest

from app.core.events import EventContext
from app.workspace import AuditLimits, AuditTrail, FileChange, FileOpLimits, file_ops

RAIZ = Path(__file__).resolve().parents[2]
CONTEXTO = EventContext(
    correlation_id="correlacao-teste-008",
    task_id="HCW-05-008",
    agent="teste",
    phase="5",
)
SEGREDO_FALSO = "sk-chave-falsa-para-teste"

WORKER = """
import sys
import time
from pathlib import Path

repo, raiz = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)

from app.core.events import EventContext
from app.workspace import AuditLimits, AuditTrail, FileChange, FileOpLimits
import app.workspace.file_ops as file_ops

def bloquear(origem, destino):
    print("PRONTO", flush=True)
    time.sleep(60)


file_ops._substituir = bloquear
raiz = Path(raiz)
auditoria = AuditTrail(raiz, limits=AuditLimits(max_chars=240, max_audit_bytes=1_000_000))
contexto = EventContext(
    correlation_id="correlacao-kill",
    task_id="HCW-05-008",
    agent="teste",
    phase="5",
)
file_ops.apply_atomic(
    raiz,
    (FileChange(path="estado.txt", data=b"novo"),),
    context=contexto,
    audit=auditoria,
    limits=FileOpLimits(max_chars=240, max_file_bytes=1000, max_total_bytes=10000, max_files=10),
)
"""


def _limites() -> FileOpLimits:
    """Devolve limites pequenos e suficientes para os testes."""
    return FileOpLimits(
        max_chars=240,
        max_file_bytes=1000,
        max_total_bytes=10000,
        max_files=10,
    )


def _auditoria(raiz: Path) -> AuditTrail:
    """Cria a auditoria do workspace de teste."""
    return AuditTrail(
        raiz,
        limits=AuditLimits(max_chars=240, max_audit_bytes=1_000_000),
    )


def _preparar(tmp_path: Path) -> Path:
    """Cria um workspace isolado para cada teste."""
    raiz = tmp_path / "workspace"
    raiz.mkdir()
    return raiz


def _eventos(auditoria: AuditTrail) -> list[dict[str, object]]:
    """Lê os eventos gravados como JSON."""
    return [evento.to_dict() for evento in auditoria.read()]


def test_escrita_atomica_gera_evento_com_contexto_sem_conteudo(tmp_path: Path) -> None:
    """Cada escrita fica registada com rastreabilidade e sem conteúdo."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)
    conteudo = f"token = {SEGREDO_FALSO}\n".encode()

    file_ops.apply_atomic(
        raiz,
        (FileChange(path="src/main.py", data=conteudo),),
        context=CONTEXTO,
        audit=auditoria,
        limits=_limites(),
    )

    assert (raiz / "src/main.py").read_bytes() == conteudo
    escritas = [evento for evento in _eventos(auditoria) if evento["kind"] == "workspace.write"]
    assert len(escritas) == 1
    assert escritas[0]["task_id"] == CONTEXTO.task_id
    assert escritas[0]["correlation_id"] == CONTEXTO.correlation_id
    assert escritas[0]["agent"] == CONTEXTO.agent
    assert escritas[0]["phase"] == CONTEXTO.phase
    dados = cast("dict[str, object]", escritas[0]["data"])
    assert dados["path"] == "src/main.py"
    assert dados["sha256"] == hashlib.sha256(conteudo).hexdigest()
    serializado = json.dumps(_eventos(auditoria), ensure_ascii=False)
    assert SEGREDO_FALSO not in serializado
    assert "token =" not in serializado


def test_interrupcao_antes_do_commit_descarta_staging_e_mantem_estado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Uma falha antes do commit não altera ficheiros nem deixa resíduos."""
    raiz = _preparar(tmp_path)
    (raiz / "estado.txt").write_bytes(b"original")
    auditoria = _auditoria(raiz)

    def interromper(*args: object, **kwargs: object) -> None:
        """Simula uma interrupção antes da marcação do commit."""
        raise RuntimeError("interrompido")

    monkeypatch.setattr(file_ops, "_registar_commit", interromper)
    with pytest.raises(file_ops.FileOpsError):
        file_ops.apply_atomic(
            raiz,
            (FileChange(path="estado.txt", data=b"novo"),),
            context=CONTEXTO,
            audit=auditoria,
            limits=_limites(),
        )

    assert (raiz / "estado.txt").read_bytes() == b"original"
    relatorio = file_ops.recover_workspace(
        raiz,
        context=CONTEXTO,
        audit=auditoria,
        limits=_limites(),
    )
    assert relatorio.restored_files == 0
    assert relatorio.discarded == 1
    staging = raiz / ".file-ops" / "staging"
    assert not staging.exists() or not any(staging.iterdir())


def test_processo_kill_depois_do_commit_e_recuperado(tmp_path: Path) -> None:
    """Um processo morto depois do commit é retomado até ao estado válido."""
    raiz = _preparar(tmp_path)
    (raiz / "estado.txt").write_bytes(b"original")
    ambiente = dict(os.environ)
    ambiente["PYTHONPATH"] = str(RAIZ)
    processo = subprocess.Popen(
        [sys.executable, "-c", WORKER, str(RAIZ), str(raiz)],
        cwd=raiz,
        env=ambiente,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    fila: Queue[str] = Queue()

    def ler_saida() -> None:
        """Encaminha a saída do processo para a fila de sincronização."""
        if processo.stdout is not None:
            for linha in processo.stdout:
                fila.put(linha.strip())

    leitor = Thread(target=ler_saida, daemon=True)
    leitor.start()
    try:
        sinal = fila.get(timeout=30)
    except Empty as exc:
        processo.kill()
        processo.wait(timeout=10)
        pytest.fail(f"O worker não sinalizou a interrupção: {exc}")
    finally:
        if processo.poll() is None:
            processo.kill()
        processo.wait(timeout=10)
        leitor.join(timeout=5)

    assert sinal == "PRONTO"
    assert (raiz / "estado.txt").read_bytes() == b"original"
    auditoria = _auditoria(raiz)
    relatorio = file_ops.recover_workspace(
        raiz,
        context=CONTEXTO,
        audit=auditoria,
        limits=_limites(),
    )
    assert relatorio.restored_files == 1
    assert (raiz / "estado.txt").read_bytes() == b"novo"
    eventos = _eventos(auditoria)
    assert any(evento["kind"] == "workspace.recovery" for evento in eventos)


def test_recuperacao_sem_pendencias_e_idempotente(tmp_path: Path) -> None:
    """Depois de uma escrita concluída não há trabalho de recuperação."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)
    file_ops.apply_atomic(
        raiz,
        (FileChange(path="estado.txt", data=b"novo"),),
        context=CONTEXTO,
        audit=auditoria,
        limits=_limites(),
    )

    relatorio = file_ops.recover_workspace(
        raiz,
        context=CONTEXTO,
        audit=auditoria,
        limits=_limites(),
    )

    assert relatorio.operation_ids == ()
    assert relatorio.restored_files == 0
    assert relatorio.discarded == 0
    assert (raiz / "estado.txt").read_bytes() == b"novo"


def test_escrita_fora_da_raiz_e_recusada(tmp_path: Path) -> None:
    """Travessia não cria ficheiros fora do workspace."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)
    alvo = tmp_path / "fora.txt"

    with pytest.raises(file_ops.FileOpsError):
        file_ops.apply_atomic(
            raiz,
            (FileChange(path="../fora.txt", data=b"novo"),),
            context=CONTEXTO,
            audit=auditoria,
            limits=_limites(),
        )

    assert not alvo.exists()
    assert not any(evento["kind"] == "workspace.write" for evento in _eventos(auditoria))


def test_ligacao_para_fora_e_recusada(tmp_path: Path) -> None:
    """Uma ligação existente não é usada para escrever fora da raiz."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)
    alvo = tmp_path / "fora.txt"
    ligacao = raiz / "ligacao"
    try:
        ligacao.symlink_to(tmp_path, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"O ambiente não permite criar ligações: {exc}")

    with pytest.raises(file_ops.FileOpsError):
        file_ops.apply_atomic(
            raiz,
            (FileChange(path="ligacao/fora.txt", data=b"novo"),),
            context=CONTEXTO,
            audit=auditoria,
            limits=_limites(),
        )

    assert not alvo.exists()


def test_auditoria_ignora_campos_fora_da_lista_segura(tmp_path: Path) -> None:
    """Campos não autorizados não chegam ao registo de auditoria."""
    raiz = _preparar(tmp_path)
    auditoria = _auditoria(raiz)

    auditoria.record(
        CONTEXTO,
        kind="workspace.write",
        message="escrita verificada",
        data={
            "path": "estado.txt",
            "sha256": hashlib.sha256(b"novo").hexdigest(),
            "size": 4,
            "content": SEGREDO_FALSO,
            "token": "sk-outro-valor-falso",
        },
    )

    evento = _eventos(auditoria)[0]
    assert set(cast("dict[str, object]", evento["data"])) == {"path", "sha256", "size"}
    serializado = json.dumps(_eventos(auditoria), ensure_ascii=False)
    assert SEGREDO_FALSO not in serializado
    assert "sk-outro-valor-falso" not in serializado
