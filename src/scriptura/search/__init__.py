"""SQLite FTS5 lexical search — the always-available baseline retrieval tier.

Depends on ``scriptura.core`` and ``scriptura.storage``.
"""

from __future__ import annotations

from .fts import (
    TOKENIZER,
    ClaimHit,
    CorpusHit,
    FtsIndex,
    escape_match,
    phrase_query,
    prefix_query,
)

__all__ = [
    "TOKENIZER",
    "ClaimHit",
    "CorpusHit",
    "FtsIndex",
    "escape_match",
    "phrase_query",
    "prefix_query",
]
