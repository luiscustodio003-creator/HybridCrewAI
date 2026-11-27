"""API pública do módulo de workspace."""

from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.scanner import (
    IgnoredFile,
    IgnoreReason,
    WorkspaceScan,
    scan_workspace,
)

__all__ = [
    "IgnoreReason",
    "IgnoredFile",
    "WorkspacePathError",
    "WorkspaceScan",
    "scan_workspace",
    "validate_workspace_path",
]
