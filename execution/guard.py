"""Guardas aplicadas aos subprocessos Python do executor simples."""

from __future__ import annotations

import os
from pathlib import Path

GUARDA_SUBPROCESSO = '''"""Guarda aplicada aos subprocessos Python do executor."""

import builtins
import os
import socket
import sys
from pathlib import Path

_RAIZ = Path(os.environ["HCW_EXEC_WORKSPACE"]).resolve()
_RAIZES_LEITURA = (
    _RAIZ,
    Path(sys.base_prefix).resolve(),
    Path(sys.prefix).resolve(),
)
_DEVNULL = os.fsdecode(os.devnull).lower()
_DEVNULL_ABSOLUTO = os.path.abspath(os.devnull).lower()


def _dentro(caminho, raiz):
    try:
        return caminho.resolve().is_relative_to(raiz)
    except (OSError, RuntimeError):
        return False


def _verificar(caminho, escrita):
    if not isinstance(caminho, (str, bytes, os.PathLike)):
        return
    texto = os.fsdecode(caminho)
    destino = Path(texto).resolve()
    basename = os.path.basename(texto).lower()
    if texto.lower() in (_DEVNULL, _DEVNULL_ABSOLUTO) or basename in (
        os.path.basename(os.devnull).lower(),
        "null",
    ):
        return
    if not _dentro(destino, _RAIZ):
        permitido = escrita or not any(
            _dentro(destino, raiz) for raiz in _RAIZES_LEITURA
        )
        if permitido:
            raise PermissionError("Acesso a ficheiros fora da pasta autorizada.")


_abrir = builtins.open


def _open(caminho, modo="r", *args, **kwargs):
    escrita = any(marca in str(modo) for marca in ("w", "a", "x", "+"))
    _verificar(caminho, escrita)
    return _abrir(caminho, modo, *args, **kwargs)


builtins.open = _open
_abrir_fd = os.open


def _open_fd(caminho, sinalizadores, *args, **kwargs):
    mascara = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
    _verificar(caminho, bool(sinalizadores & mascara))
    return _abrir_fd(caminho, sinalizadores, *args, **kwargs)


os.open = _open_fd


def _negar_rede(*args, **kwargs):
    raise PermissionError("Rede desactivada para subprocessos do executor.")


socket.getaddrinfo = _negar_rede
socket.create_connection = _negar_rede
socket.socket.connect = _negar_rede
socket.socket.connect_ex = _negar_rede
'''


def ambiente_limpo(destino: Path) -> dict[str, str]:
    """Devolve ambiente mínimo sem credenciais nem variáveis HCW_* além da pasta."""
    ambiente = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(destino),
        "HCW_EXEC_WORKSPACE": str(destino),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    if os.name == "nt":
        for nome in ("SystemRoot", "COMSPEC"):
            if nome in os.environ:
                ambiente[nome] = os.environ[nome]
        ambiente["TEMP"] = str(destino)
        ambiente["TMP"] = str(destino)
    else:
        ambiente["HOME"] = str(destino)
        ambiente["TMPDIR"] = str(destino)
    return ambiente
