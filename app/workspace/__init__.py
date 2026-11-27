"""API pública do módulo de workspace."""

from app.workspace.paths import WorkspacePathError, validate_workspace_path

__all__ = ["WorkspacePathError", "validate_workspace_path"]
