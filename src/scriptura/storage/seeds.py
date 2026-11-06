"""Reference-data seeding: books and canon profiles (NOT corpus text).

Seeding the book registry and canon profiles is reference metadata, not corpus
ingestion: no edition text, no licence gate, no dataset. It makes `make db`
produce a usable empty knowledge base.
"""

from __future__ import annotations

import sqlite3

from ..core.hashing import mint_identifier
from ..core.reference import BOOKS, CANON_PROFILES

__all__ = ["seed_reference_data"]


def seed_reference_data(conn: sqlite3.Connection, actor: str = "scriptura-seed") -> dict[str, int]:
    """Insert books, canon profiles, and membership. Idempotent by key."""
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    books = profiles = memberships = 0
    for book in BOOKS.values():
        bid = mint_identifier("scriptura", "book", {"key": book.key})
        cur = conn.execute(
            "insert or ignore into books(id, key, name_en, chapters, testament, notes)"
            " values (?,?,?,?,?,?)",
            (bid, book.key, book.name_en, book.chapters, book.testament, book.notes or None),
        )
        books += cur.rowcount
    for profile in CANON_PROFILES.values():
        pid = mint_identifier("scriptura", "profile", {"key": profile.key})
        cur = conn.execute(
            "insert or ignore into canon_profiles(id, key, name, description)"
            " values (?,?,?,?)",
            (pid, profile.key, profile.name, profile.description),
        )
        profiles += cur.rowcount
        for position, key in enumerate(profile.book_keys):
            book = BOOKS[key]
            bid = mint_identifier("scriptura", "book", {"key": book.key})
            cur = conn.execute(
                "insert or ignore into book_canon_membership(book_id, profile_id, position)"
                " values (?,?,?)",
                (bid, pid, position),
            )
            memberships += cur.rowcount
    void = stamp, actor
    _ = void
    return {"books": books, "profiles": profiles, "memberships": memberships}
