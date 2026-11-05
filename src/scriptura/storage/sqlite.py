"""SQLite connection management, pragmas, and the platform capability probe.

Normative source: BKB-ARCH-001 section 6; BKB-DATA-001 section 6; ADR-0001;
ADR-0009.

The knowledge base is a single SQLite file. There is no server, no credentials, and
no listening socket.

Foreign keys are enforced on EVERY connection (rule S2). The capability probe fails
LOUDLY if the platform SQLite lacks FTS5 or JSON1, because silently degrading would
mean a search index that does not exist.
"""

from __future__ import annotations

import pathlib
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from ..core.errors import CapabilityError, StorageError

__all__ = [
    "MIN_SQLITE_VERSION",
    "REQUIRED_COMPILE_OPTIONS",
    "PlatformCapabilities",
    "probe_capabilities",
    "capability_report",
    "require_capabilities",
    "connect",
    "connection",
    "apply_pragmas",
    "journal_mode",
    "close_quietly",
]

#: The minimum SQLite version Scriptura supports. FTS5 ``remove_diacritics 2`` and
#: the JSON1 functions are required; both are long-standing, but a floor is stated so
#: that a failure names the cause rather than presenting as a syntax error.
MIN_SQLITE_VERSION = (3, 20, 0)

#: Compile options that MUST be present. Enforced by :func:`require_capabilities`.
REQUIRED_COMPILE_OPTIONS = ("ENABLE_FTS5",)


@dataclass(frozen=True)
class PlatformCapabilities:
    """What the platform SQLite can actually do.

    Attributes:
        sqlite_version: The SQLite library version string.
        version_tuple: The version as integers, for comparison.
        compile_options: Compile options reported by ``pragma_compile_options``.
        fts5: Whether FTS5 is compiled in.
        json1: Whether the JSON1 functions are functional.
        unicode61_diacritics: Whether ``unicode61 remove_diacritics 2`` works. This is
            what makes accent-insensitive search over polytonic Greek and pointed
            Hebrew possible WITHOUT altering the stored text (ADR-0009).
        fts5_functional: Whether an FTS5 table can actually be created and queried.
        missing: Compile options that are required but absent.
    """

    sqlite_version: str
    version_tuple: tuple[int, ...]
    compile_options: tuple[str, ...]
    fts5: bool
    json1: bool
    unicode61_diacritics: bool
    fts5_functional: bool
    missing: tuple[str, ...]

    @property
    def satisfied(self) -> bool:
        """Whether every required capability is present."""
        return (
            not self.missing
            and self.version_tuple >= MIN_SQLITE_VERSION
            and self.fts5
            and self.json1
            and self.unicode61_diacritics
            and self.fts5_functional
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "sqlite_version": self.sqlite_version,
            "version_tuple": list(self.version_tuple),
            "min_sqlite_version": list(MIN_SQLITE_VERSION),
            "fts5": self.fts5,
            "json1": self.json1,
            "unicode61_diacritics": self.unicode61_diacritics,
            "fts5_functional": self.fts5_functional,
            "missing_compile_options": list(self.missing),
            "satisfied": self.satisfied,
        }


def _parse_version(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in text.split("."):
        digits = ""
        for char in chunk:
            if char.isdigit():
                digits += char
            else:
                break
        if digits:
            parts.append(int(digits))
    return tuple(parts) or (0,)


def probe_capabilities(conn: sqlite3.Connection | None = None) -> PlatformCapabilities:
    """Probe what the platform SQLite can do.

    Uses an in-memory connection when *conn* is not supplied, so probing never touches
    a real database.
    """
    own = conn is None
    if own:
        conn = sqlite3.connect(":memory:")
    try:
        version = str(conn.execute("select sqlite_version()").fetchone()[0])
        options = tuple(
            sorted(
                str(row[0])
                for row in conn.execute("select compile_options from pragma_compile_options")
            )
        )
        fts5 = "ENABLE_FTS5" in options

        try:
            conn.execute("select json(?)", ('{"a":1}',)).fetchone()
            json1 = True
        except sqlite3.Error:
            json1 = False

        unicode61 = False
        fts5_functional = False
        if fts5:
            try:
                conn.execute("drop table if exists _scriptura_probe")
                conn.execute(
                    "create virtual table _scriptura_probe using fts5"
                    "(x, tokenize='unicode61 remove_diacritics 2')"
                )
                unicode61 = True
                conn.execute("insert into _scriptura_probe(x) values (?)", ("lógos",))
                row = conn.execute(
                    "select count(*) from _scriptura_probe where _scriptura_probe match ?",
                    ("logos",),
                ).fetchone()
                fts5_functional = bool(row and row[0] >= 1)
                conn.execute("drop table if exists _scriptura_probe")
            except sqlite3.Error:
                conn.execute("drop table if exists _scriptura_probe")

        missing = tuple(opt for opt in REQUIRED_COMPILE_OPTIONS if opt not in options)
        return PlatformCapabilities(
            sqlite_version=version,
            version_tuple=_parse_version(version),
            compile_options=options,
            fts5=fts5,
            json1=json1,
            unicode61_diacritics=unicode61,
            fts5_functional=fts5_functional,
            missing=missing,
        )
    finally:
        if own:
            conn.close()


def capability_report(conn: sqlite3.Connection | None = None) -> str:
    """Return a human-readable capability report."""
    caps = probe_capabilities(conn)
    lines = [
        f"SQLite {caps.sqlite_version} (minimum required: "
        f"{'.'.join(str(p) for p in MIN_SQLITE_VERSION)})",
        f"  FTS5 compiled in            : {caps.fts5}",
        f"  FTS5 create+query functional: {caps.fts5_functional}",
        f"  JSON1 functional            : {caps.json1}",
        f"  unicode61 remove_diacritics 2: {caps.unicode61_diacritics}",
        f"  missing required options    : {', '.join(caps.missing) or '(none)'}",
        f"  SATISFIED                   : {caps.satisfied}",
    ]
    return "\n".join(lines)


def require_capabilities(conn: sqlite3.Connection | None = None) -> PlatformCapabilities:
    """Probe and raise if any required capability is absent.

    Fails LOUDLY. A silently missing FTS5 would mean a search index that does not
    exist, which is worse than a startup failure.

    Raises:
        CapabilityError: naming every missing capability.
    """
    caps = probe_capabilities(conn)
    if caps.satisfied:
        return caps
    problems: list[str] = []
    if caps.version_tuple < MIN_SQLITE_VERSION:
        problems.append(
            f"SQLite {caps.sqlite_version} is older than the required "
            f"{'.'.join(str(p) for p in MIN_SQLITE_VERSION)}"
        )
    if caps.missing:
        problems.append(
            "missing required compile options: " + ", ".join(caps.missing)
        )
    if not caps.fts5_functional:
        problems.append("FTS5 cannot create and query a virtual table")
    if not caps.json1:
        problems.append("JSON1 functions are not available")
    if not caps.unicode61_diacritics:
        problems.append(
            "the unicode61 tokenizer with 'remove_diacritics 2' is not available; "
            "accent-insensitive search over Greek and Hebrew requires it (ADR-0009)"
        )
    raise CapabilityError(
        "This platform's SQLite does not satisfy Scriptura's requirements:\n  - "
        + "\n  - ".join(problems)
    )


def apply_pragmas(
    conn: sqlite3.Connection,
    journal: str = "WAL",
    synchronous: str = "NORMAL",
    foreign_keys: bool = True,
) -> None:
    """Apply Scriptura's standard pragmas to *conn*.

    ``foreign_keys`` is ON by default and on every connection (rule S2). It is a
    per-connection setting in SQLite, so it must be applied on EVERY connection;
    forgetting it silently disables referential integrity.
    """
    conn.execute(f"pragma journal_mode = {journal}")
    conn.execute(f"pragma synchronous = {synchronous}")
    conn.execute(f"pragma foreign_keys = {'ON' if foreign_keys else 'OFF'}")
    # Deterministic ordering for reproducible query results.
    conn.execute("pragma legacy_alter_table = OFF")


def journal_mode(conn: sqlite3.Connection) -> str:
    """Return the current journal mode of *conn*."""
    return str(conn.execute("pragma journal_mode").fetchone()[0])


def connect(
    path: str | pathlib.Path | None = None,
    *,
    journal: str = "WAL",
    read_only: bool = False,
    check_capabilities: bool = True,
) -> sqlite3.Connection:
    """Open a Scriptura database connection.

    Args:
        path: Database file path, or ``None``/``":memory:"`` for an in-memory database.
        journal: Journal mode. ``WAL`` for concurrent read/write; ``DELETE`` for an
            archival snapshot.
        read_only: Open the file read-only. Requires an existing file.
        check_capabilities: Probe platform capabilities first. On by default.

    Returns:
        A connection with ``row_factory`` set, pragmas applied, and foreign keys on.

    Raises:
        CapabilityError: if capabilities are unsatisfied and *check_capabilities*.
        StorageError: if the database cannot be opened.
    """
    if check_capabilities:
        require_capabilities()

    target = ":memory:" if path is None else str(path)
    if read_only:
        if target == ":memory:":
            raise StorageError("Cannot open an in-memory database read-only.")
        if not pathlib.Path(target).is_file():
            raise StorageError(
                f"Cannot open {target!r} read-only: the file does not exist."
            )
        uri = f"file:{pathlib.Path(target).resolve()}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
        except sqlite3.Error as exc:
            raise StorageError(f"Could not open {target!r} read-only: {exc}") from exc
        # A read-only connection cannot set journal_mode; skip write pragmas.
        conn.execute("pragma foreign_keys = ON")
    else:
        try:
            conn = sqlite3.connect(target)
        except sqlite3.Error as exc:
            raise StorageError(f"Could not open {target!r}: {exc}") from exc
        apply_pragmas(conn, journal=journal)

    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection(
    path: str | pathlib.Path | None = None, *, journal: str = "WAL",
    read_only: bool = False, check_capabilities: bool = True,
) -> Iterator[sqlite3.Connection]:
    """Context manager yielding a connection and closing it on exit.

    Commits on clean exit and rolls back on exception, so a failed operation never
    leaves partial state (BKB-CORPUS-001 rule R1).
    """
    conn = connect(
        path, journal=journal, read_only=read_only, check_capabilities=check_capabilities
    )
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()


def close_quietly(conn: sqlite3.Connection | None) -> None:
    """Close *conn*, ignoring errors. For cleanup paths only."""
    if conn is None:
        return
    try:
        conn.close()
    except sqlite3.Error:  # pragma: no cover - defensive
        pass
