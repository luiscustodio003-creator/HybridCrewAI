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
from app.workspace.rollback import (
    RollbackError,
    RollbackReport,
    UndoReport,
    load_snapshot,
    rollback,
    undo_rollback,
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
from app.workspace.snapshot import (
    Snapshot,
    SnapshotEntry,
    SnapshotError,
    SnapshotLimits,
    create_snapshot,
    inventory_workspace,
    snapshot_digest,
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
    "RollbackError",
    "RollbackReport",
    "SensitiveFile",
    "SensitiveReason",
    "Snapshot",
    "SnapshotEntry",
    "SnapshotError",
    "SnapshotLimits",
    "UndoReport",
    "WorkspacePathError",
    "WorkspaceScan",
    "classify_sensitive",
    "create_snapshot",
    "ingest_zip",
    "inventory_workspace",
    "load_snapshot",
    "quarantine_attachment",
    "release_quarantine",
    "rollback",
    "scan_workspace",
    "snapshot_digest",
    "undo_rollback",
    "validate_workspace_path",
]
