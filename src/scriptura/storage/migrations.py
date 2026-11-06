"""Forward-only migration runner with an applied-migrations ledger.

Normative source: BKB-DATA-001 section 8.

Migrations are ADDITIVE and FORWARD-ONLY. An applied migration is never edited. A
ledger hash mismatch is a Critical integrity incident, because it indicates that an
applied migration was edited after the fact.

There are no down-migrations. Reversal is by a new forward migration.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from ..core.errors import IntegrityError, MigrationError

__all__ = [
    "MIGRATIONS_DIR",
    "Migration",
    "AppliedMigration",
    "discover_migrations",
    "ensure_ledger",
    "applied_migrations",
    "pending_migrations",
    "apply_migrations",
    "verify_ledger",
    "schema_version",
]

#: Where migration files live.
MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent / "migrations"

_MIGRATION_RE = re.compile(r"^(?P<seq>\d{4})_(?P<name>[a-z0-9_]+)\.sql$")


@dataclass(frozen=True)
class Migration:
    """A migration file on disk."""

    sequence: int
    name: str
    path: pathlib.Path
    sql: str
    sha256: str

    @property
    def filename(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class AppliedMigration:
    """A migration recorded in the ledger."""

    sequence: int
    name: str
    applied_at: str
    sha256: str


def discover_migrations(directory: pathlib.Path | None = None) -> tuple[Migration, ...]:
    """Return migrations on disk, ordered by sequence.

    Raises:
        MigrationError: if a ``.sql`` file does not match ``NNNN_name.sql``, or two
            files share a sequence number.
    """
    base = pathlib.Path(directory) if directory is not None else MIGRATIONS_DIR
    if not base.is_dir():
        raise MigrationError(f"Migrations directory does not exist: {base}")

    found: list[Migration] = []
    seen: dict[int, str] = {}
    for path in sorted(base.iterdir()):
        if path.suffix != ".sql" or not path.is_file():
            continue
        match = _MIGRATION_RE.match(path.name)
        if match is None:
            raise MigrationError(
                f"Migration file {path.name!r} does not match the required form "
                f"'NNNN_name.sql' (four-digit sequence, then lower-case name)."
            )
        sequence = int(match.group("seq"))
        if sequence in seen:
            raise MigrationError(
                f"Duplicate migration sequence {sequence}: {seen[sequence]!r} and "
                f"{path.name!r}. Sequences must be unique."
            )
        sql = path.read_text(encoding="utf-8")
        seen[sequence] = path.name
        found.append(
            Migration(
                sequence=sequence,
                name=match.group("name"),
                path=path,
                sql=sql,
                sha256=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(sorted(found, key=lambda m: m.sequence))


def ensure_ledger(conn: sqlite3.Connection) -> None:
    """Create the migration ledger if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            sequence    INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TEXT NOT NULL,
            sha256      TEXT NOT NULL
        )
        """
    )


def applied_migrations(conn: sqlite3.Connection) -> tuple[AppliedMigration, ...]:
    """Return the ledger contents, ordered by sequence."""
    ensure_ledger(conn)
    rows = conn.execute(
        "select sequence, name, applied_at, sha256 from schema_migrations order by sequence"
    ).fetchall()
    return tuple(
        AppliedMigration(
            sequence=int(row[0]), name=str(row[1]),
            applied_at=str(row[2]), sha256=str(row[3]),
        )
        for row in rows
    )


def pending_migrations(
    conn: sqlite3.Connection, directory: pathlib.Path | None = None
) -> tuple[Migration, ...]:
    """Return migrations on disk that have not been applied."""
    applied = {m.sequence for m in applied_migrations(conn)}
    return tuple(m for m in discover_migrations(directory) if m.sequence not in applied)


def apply_migrations(
    conn: sqlite3.Connection, directory: pathlib.Path | None = None
) -> tuple[Migration, ...]:
    """Apply all pending migrations, in order, each inside a transaction.

    Re-applying an already-applied migration is a no-op, not an error (rule M6).
    A migration that has been applied but whose file hash no longer matches the ledger
    is a Critical integrity incident (rule M7) and raises before anything is applied.

    Returns:
        The migrations that were applied by this call.

    Raises:
        IntegrityError: if an applied migration's file hash does not match the ledger.
        MigrationError: if a migration fails to execute.
    """
    verify_ledger(conn, directory)
    ensure_ledger(conn)

    applied_now: list[Migration] = []
    for migration in pending_migrations(conn, directory):
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            conn.execute("begin")
            conn.executescript(migration.sql)
            conn.execute(
                "insert into schema_migrations(sequence, name, applied_at, sha256) "
                "values (?, ?, ?, ?)",
                (migration.sequence, migration.name, started, migration.sha256),
            )
            conn.execute("commit")
            conn.execute("pragma foreign_keys = ON")
        except sqlite3.Error as exc:
            # executescript() commits any pending transaction before running, so
            # a failure may leave no active transaction. Rollback defensively and
            # surface the ORIGINAL error, never a secondary rollback error.
            try:
                conn.execute("rollback")
            except sqlite3.Error:
                pass
            # Migration SQL may toggle PRAGMA foreign_keys for table rebuilds;
            # always re-assert enforcement so a failed migration never leaves the
            # connection (or any later use of it) running without FK checks.
            try:
                conn.execute("pragma foreign_keys = ON")
            except sqlite3.Error:
                pass
            raise MigrationError(
                f"Migration {migration.filename} failed: {exc}"
            ) from exc
        applied_now.append(migration)
    return tuple(applied_now)


def verify_ledger(
    conn: sqlite3.Connection, directory: pathlib.Path | None = None
) -> tuple[AppliedMigration, ...]:
    """Verify that applied migrations still hash to their ledger values.

    Returns:
        The ledger contents.

    Raises:
        IntegrityError: naming every mismatch. A mismatch indicates that an applied
            migration was edited after the fact, which is prohibited (rule M2).
    """
    ledger = applied_migrations(conn)
    if not ledger:
        return ledger

    on_disk = {m.sequence: m for m in discover_migrations(directory)}
    problems: list[str] = []
    for record in ledger:
        current = on_disk.get(record.sequence)
        if current is None:
            problems.append(
                f"sequence {record.sequence} ({record.name}) is recorded as applied but "
                f"no migration file exists for it"
            )
            continue
        if current.sha256 != record.sha256:
            problems.append(
                f"{current.filename} has been EDITED after being applied "
                f"(ledger sha256 {record.sha256[:12]}..., file sha256 "
                f"{current.sha256[:12]}...)"
            )
        if current.name != record.name:
            problems.append(
                f"sequence {record.sequence} was applied as {record.name!r} but the file "
                f"is now named {current.name!r}"
            )
    if problems:
        raise IntegrityError(
            "Migration ledger verification FAILED. Applied migrations are never edited; "
            "correction is by a NEW forward migration.\n  - " + "\n  - ".join(problems)
        )
    return ledger


def schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration sequence, or 0 if none."""
    ledger = applied_migrations(conn)
    return max((m.sequence for m in ledger), default=0)
