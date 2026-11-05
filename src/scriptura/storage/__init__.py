"""SQLite storage: connection management and forward-only migrations.

Depends on ``scriptura.core`` only.
"""

from __future__ import annotations

from .migrations import (
    MIGRATIONS_DIR,
    AppliedMigration,
    Migration,
    applied_migrations,
    apply_migrations,
    discover_migrations,
    ensure_ledger,
    pending_migrations,
    schema_version,
    verify_ledger,
)
from .sqlite import (
    PlatformCapabilities,
    capability_report,
    connect,
    connection,
    probe_capabilities,
    require_capabilities,
)

__all__ = [
    "MIGRATIONS_DIR",
    "AppliedMigration",
    "Migration",
    "applied_migrations",
    "apply_migrations",
    "discover_migrations",
    "ensure_ledger",
    "pending_migrations",
    "schema_version",
    "verify_ledger",
    "PlatformCapabilities",
    "capability_report",
    "connect",
    "connection",
    "probe_capabilities",
    "require_capabilities",
]
