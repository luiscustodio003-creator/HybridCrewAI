"""API pública do módulo de workspace."""

from app.workspace.archive import (
    ArchiveEntry,
    ArchiveError,
    ArchiveLimits,
    ArchiveReport,
    ingest_zip,
)
from app.workspace.paths import WorkspacePathError, validate_workspace_path
from app.workspace.quarantine import (
    QuarantinedAttachment,
    QuarantineError,
    QuarantineLimits,
    quarantine_attachment,
    release_quarantine,
)
from app.workspace.scanner import (
    IgnoredFile,
    IgnoreReason,
    WorkspaceScan,
    scan_workspace,
)
from app.workspace.sensitive import (
    SensitiveFile,
    SensitiveReason,
    classify_sensitive,
)

__all__ = [
    "ArchiveEntry",
    "ArchiveError",
    "ArchiveLimits",
    "ArchiveReport",
    "IgnoreReason",
    "IgnoredFile",
    "QuarantinedAttachment",
    "QuarantineError",
    "QuarantineLimits",
    "SensitiveFile",
    "SensitiveReason",
    "WorkspacePathError",
    "WorkspaceScan",
    "classify_sensitive",
    "ingest_zip",
    "quarantine_attachment",
    "release_quarantine",
    "scan_workspace",
    "validate_workspace_path",
]
