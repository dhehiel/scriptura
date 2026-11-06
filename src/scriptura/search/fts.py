"""SQLite FTS5 lexical search.

Normative source: BKB-ARCH-001 section 7; ADR-0009 (corrected); ADR-0011.

FTS5 is the BASELINE retrieval tier and is always available.

Search modes (``diacritics`` parameter). These are precise, and NONE of them is
byte-exact at the index level -- FTS5 tokenizes by definition:

- ``exact``: match against the STORED-FORM index column with NO application-level
  folding. The FTS tokenizer (``unicode61``) still normalizes case and strips its
  own Latin diacritics -- that is TOKENIZER NORMALIZATION, not byte-exactness.
- ``folded``: match against the EXPLICITLY FOLDED index column, where the query is
  transformed with the same NFD fold used at index time
  (:func:`scriptura.core.text.fold_diacritics`).
- ``both`` (default): evaluate BOTH paths and deduplicate. Union, never
  transliteration: Greek matches Greek, Hebrew matches Hebrew.

Byte-exact equality is NOT an FTS feature. Where it is required, verify it in
application code with :func:`verify_byte_exact`, comparing the STORED string to
the candidate string.

CRITICAL: diacritic folding is a SEARCH affordance only. The stored text in
``corpus_records`` and ``claims`` is NEVER altered (BKB-DATA-001 rule U6).
VERIFIED ON SQLITE 3.40.1: the tokenizer's ``remove_diacritics 2`` folds LATIN
diacritics only; Greek polytonic and Hebrew niqqud are folded EXPLICITLY into a
separate index column (ADR-0009 corrected).

Search results ALWAYS carry epistemic layer, record id, and the non-authoritative
flag. A search never silently merges layers; layer filtering is a first-class
parameter. Filtering and pagination are applied AFTER the candidate fetch so that
a premature inner LIMIT cannot drop relevant results.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from ..core.errors import SearchError
from ..core.layers import EpistemicLayer, coerce_layer
from ..core.text import fold_diacritics

__all__ = [
    "TOKENIZER",
    "DIACRITIC_MODES",
    "DiacriticMode",
    "CorpusHit",
    "ClaimHit",
    "FtsIndex",
    "escape_match",
    "phrase_query",
    "prefix_query",
    "fold_diacritics",
    "verify_byte_exact",
]

#: The tokenizer configuration. ``remove_diacritics 2`` folds LATIN diacritics for
#: matching while leaving stored text untouched.
TOKENIZER = "unicode61 remove_diacritics 2"

#:
# VERIFIED ON SQLITE 3.40.1: ``remove_diacritics 2`` does NOT fold Greek polytonic
# diacritics or Hebrew niqqud. ``\u03bb\u03cc\u03b3\u03bf\u03c2`` does not match ``\u03bb\u03bf\u03b3\u03bf\u03c2``, and pointed Hebrew does
# not match unpointed Hebrew. Accent-insensitive search over Greek and Hebrew is a
# hard requirement for this domain, so the folded form is computed EXPLICITLY by
# :func:`scriptura.core.text.fold_diacritics` and indexed in a separate column.
#
# The stored text in ``corpus_records`` and ``claims`` is NEVER replaced by the folded
# form (BKB-DATA-001 rule U6).

_MATCH_UNSAFE = re.compile(r'["()*:^-]')


@dataclass(frozen=True)
class CorpusHit:
    """A hit against the corpus index.

    Carries everything a retrieval result must preserve (directive section 9):
    layer, record id, edition/source, provenance, verification status, and the
    non-authoritative flag.

    ``text`` is the STORED text from ``corpus_records``, not the indexed form.
    ``verification_status`` is ``None`` for corpus records: per-record
    verification lives on ``claims``; corpus records carry dataset-level licence
    status instead.
    """

    record_id: str
    layer: str
    edition_id: str | None
    reference_display: str | None
    text: str
    rank: float
    source_uri: str | None = None
    verification_status: str | None = None
    non_authoritative: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "layer": self.layer,
            "edition_id": self.edition_id,
            "reference_display": self.reference_display,
            "text": self.text,
            "rank": self.rank,
            "source_uri": self.source_uri,
            "verification_status": self.verification_status,
            "non_authoritative": self.non_authoritative,
        }


@dataclass(frozen=True)
class ClaimHit:
    """A hit against the claim index.

    ``non_authoritative`` is always present, so an ``ai_hypothesis`` result cannot be
    presented without its flag (invariant L6).
    """

    claim_id: str
    layer: str
    non_authoritative: bool
    statement: str
    rank: float
    source_uri: str | None = None
    verification_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "layer": self.layer,
            "non_authoritative": self.non_authoritative,
            "statement": self.statement,
            "rank": self.rank,
            "source_uri": self.source_uri,
            "verification_status": self.verification_status,
        }


def escape_match(term: str) -> str:
    """Escape *term* for use as a single FTS5 MATCH token.

    Wraps the term in double quotes and escapes embedded quotes, so that punctuation
    in a search term cannot inject FTS5 query syntax. This matters: an unescaped term
    is a query-injection vector into the search index.
    """
    if not isinstance(term, str):
        raise SearchError(f"Search term must be a string, got {type(term).__name__}.")
    stripped = term.strip()
    if not stripped:
        raise SearchError("Search term must not be empty.")
    return '"' + stripped.replace('"', '""') + '"'


#: How to treat diacritics in a query. ``both`` returns the union of exact and
#: folded matches. ``exact`` matches only what was literally indexed. ``folded``
#: matches the NFD-folded form only. The default is ``both``: a query for either
#: form of a word finds both forms in storage, which is what accent-insensitive
#: search must do without altering stored text. No romanization is performed:
#: Greek is matched against Greek, Hebrew against Hebrew, Latin against Latin.
DiacriticMode = str
DIACRITIC_MODES = ("both", "exact", "folded")


def _validate_diacritic_mode(mode: str) -> str:
    if mode not in DIACRITIC_MODES:
        raise SearchError(
            f"Unknown diacritic mode {mode!r}. Valid modes: "
            + ", ".join(DIACRITIC_MODES)
            + "."
        )
    return mode


def phrase_query(phrase: str) -> str:
    """Build an FTS5 phrase query from *phrase*."""
    return escape_match(phrase)


def prefix_query(term: str) -> str:
    """Build an FTS5 prefix query from *term*.

    The term is used AS GIVEN: matching the original column uses the original term,
    and matching the folded column uses the folded term. Folding is applied by the
    caller (:meth:`FtsIndex._term`) per column, never here, so that prefix matching
    compares identical transforms on both sides. Folding affects matching only;
    stored text is never altered.
    """
    # FTS5 prefix syntax is a BARE token with a trailing star: 'term*'. The quoted
    # phrase form '"term"' matches the whole token only; '"term*"' does NOT parse
    # as a prefix query (verified on this platform's SQLite: it matches nothing,
    # silently). Prefix and phrase queries therefore have different shapes.
    # Appending the star to the UNQUOTED term keeps the query a bare-token prefix.
    if not isinstance(term, str) or not term.strip():
        raise SearchError("Prefix term must be a non-empty string.")
    stripped = term.strip()
    if any(ch in stripped for ch in '"()*:-^'):
        raise SearchError(
            f"Prefix term {stripped!r} contains FTS5 syntax characters. Prefix "
            f"queries match a single bare token; they cannot embed syntax."
        )
    return stripped + "*"


def verify_byte_exact(stored: str, candidate: str) -> bool:
    """Return whether *stored* and *candidate* are byte-exact equal.

    FTS5 cannot provide byte-exact matching: it tokenizes. Where byte-exactness
    is required, verify it HERE, in application code, by comparing the stored
    string to the candidate string directly (no tokenizer, no folding).

    Raises:
        SearchError: if either argument is not a string.
    """
    if not isinstance(stored, str) or not isinstance(candidate, str):
        raise SearchError(
            f"verify_byte_exact requires two strings, got "
            f"{type(stored).__name__} and {type(candidate).__name__}."
        )
    return stored == candidate


class FtsIndex:
    """Maintain and query the FTS5 indexes.

    Args:
        conn: An open Scriptura connection with migrations applied.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # -------------------------------------------------------------- capability ----

    def is_available(self) -> bool:
        """Return whether both FTS5 indexes exist.

        FTS5 is the baseline tier, so absence is a defect rather than a degraded mode.
        Unlike the optional semantic backend, its absence is never silently tolerated.
        """
        rows = self.conn.execute(
            "select name from sqlite_master where type='table' "
            "and name in ('corpus_fts','claim_fts')"
        ).fetchall()
        return len(rows) == 2

    def require_available(self) -> None:
        """Raise if the indexes are missing."""
        if not self.is_available():
            raise SearchError(
                "The FTS5 indexes are missing. FTS5 is the baseline retrieval tier "
                "(ADR-0009) and must be present. Apply migrations with "
                "scriptura.storage.apply_migrations()."
            )

    # ------------------------------------------------------------------ writes ----

    def index_corpus_record(
        self, *, record_id: str, layer: Any, text: str,
        edition_id: str | None = None, reference_display: str | None = None,
    ) -> None:
        """Add or replace a corpus record in the index.

        Index maintenance is transactional with the write that changes the indexed
        content (ADR-0009 rule 5). The caller is responsible for performing both in the
        same transaction.
        """
        self.require_available()
        resolved = coerce_layer(layer)
        self.conn.execute("delete from corpus_fts where record_id = ?", (record_id,))
        self.conn.execute(
            "insert into corpus_fts(record_id, layer, edition_id, reference_display, "
            "text, text_folded) values (?,?,?,?,?,?)",
            (
                record_id,
                resolved.value,
                edition_id if edition_id is not None else "",
                reference_display if reference_display is not None else "",
                text,
                fold_diacritics(text),
            ),
        )

    def index_claim(
        self, *, claim_id: str, layer: Any, statement: str, non_authoritative: bool | None = None,
    ) -> None:
        """Add or replace a claim in the index.

        ``non_authoritative`` is DERIVED from the layer when not supplied, so an
        ``ai_hypothesis`` claim cannot be indexed without its flag.
        """
        self.require_available()
        resolved = coerce_layer(layer)
        flag = (
            resolved is EpistemicLayer.AI_HYPOTHESIS
            if non_authoritative is None
            else bool(non_authoritative)
        )
        if resolved is EpistemicLayer.AI_HYPOTHESIS and not flag:
            raise SearchError(
                "An ai_hypothesis claim cannot be indexed with "
                "non_authoritative=false. The flag is mandatory (invariant L6)."
            )
        self.conn.execute("delete from claim_fts where claim_id = ?", (claim_id,))
        self.conn.execute(
            "insert into claim_fts(claim_id, layer, non_authoritative, statement, "
            "statement_folded) values (?,?,?,?,?)",
            (
                claim_id, resolved.value, 1 if flag else 0, statement,
                fold_diacritics(statement),
            ),
        )

    def reindex_corpus(self) -> int:
        """Rebuild the corpus index from ``corpus_records``.

        The content table is authoritative and the index is reconstructible from it
        (ADR-0009 rule 10).
        """
        self.require_available()
        self.conn.execute("delete from corpus_fts")
        rows = self.conn.execute(
            "select cr.id, cr.layer, cr.text, cr.edition_id, r.display "
            "from corpus_records cr left join canonical_references r "
            "on r.id = cr.reference_id"
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "insert into corpus_fts(record_id, layer, edition_id, "
                "reference_display, text, text_folded) values (?,?,?,?,?,?)",
                (row[0], row[1], row[3], row[4], row[2], fold_diacritics(row[2] or "")),
            )
        return len(rows)

    def reindex_claims(self) -> int:
        """Rebuild the claim index from ``claims``."""
        self.require_available()
        self.conn.execute("delete from claim_fts")
        rows = self.conn.execute(
            "select id, layer, non_authoritative, statement from claims"
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "insert into claim_fts(claim_id, layer, non_authoritative, statement, "
                "statement_folded) values (?,?,?,?,?)",
                (row[0], row[1], row[2], row[3], fold_diacritics(row[3] or "")),
            )
        return len(rows)

    # ----------------------------------------------------------------- queries ----

    def search_corpus(
        self, query: str, *, limit: int = 50, layers: Iterable[Any] | None = None,
        edition_id: str | None = None, prefix: bool = False,
        diacritics: str = "both",
    ) -> tuple[CorpusHit, ...]:
        """Search the corpus index.

        The returned ``text`` is the STORED text from ``corpus_records``, never the
        folded indexed form. Diacritic folding affects matching only.

        Args:
            query: The search term or phrase. Escaped before use.
            limit: Maximum hits.
            layers: Layer filter. ``None`` returns ALL layers, and each hit carries its
                own layer so the result set is never silently merged.
            edition_id: Restrict to one edition.
            prefix: Match as a prefix rather than a whole token.
            diacritics: ``both`` (default), ``exact``, or ``folded``. ``both``
                returns the union of matches on the stored text and on the
                diacritic-folded text, so a query in either form finds both.
                Union, never transliteration: Greek matches Greek, Hebrew matches
                Hebrew. No romanization is performed.

        Returns:
            Hits ordered by BM25 rank, deduplicated by record.
        """
        self.require_available()
        if limit < 1:
            raise SearchError(f"limit must be at least 1, got {limit}.")
        _validate_diacritic_mode(diacritics)
        match = self._corpus_match(query, prefix, diacritics)

        # PAGINATION AND FILTERING (directive section 9): the candidate set is
        # fetched WITHOUT an inner LIMIT, then layer/edition filters are applied,
        # then dedupe, then the caller's limit. A premature inner LIMIT would drop
        # relevant results whenever the top-ranked matches fall outside the filter.
        # record_id/layer/edition_id are UNINDEXED columns; filtering on them
        # INSIDE the FTS MATCH query silently discards rows on some builds
        # (verified on SQLite 3.40.1 for prefix queries with an OR across two
        # columns), so the filters live OUTSIDE the FTS subquery. The corpus is
        # bounded (ADR-0001), so fetching all matches before filtering is correct
        # and cost-free at this scale.
        inner = (
            "select record_id, layer, edition_id, reference_display, "
            "bm25(corpus_fts) as rank from corpus_fts where (corpus_fts match ?)"
            " order by rank"
        )
        sql = (
            "select sub.record_id, sub.layer, sub.edition_id, sub.reference_display, "
            "cr.text, sub.rank, cr.source_uri from (" + inner + ") as sub "
            "left join corpus_records cr on cr.id = sub.record_id"
        )
        params: list[Any] = [match]
        where: list[str] = []
        allowed = self._resolve_layers(layers)
        if allowed is not None:
            placeholders = ",".join("?" * len(allowed))
            where.append(f"sub.layer in ({placeholders})")
            params.extend(allowed)
        if edition_id is not None:
            where.append("sub.edition_id = ?")
            params.append(edition_id)
        if where:
            sql += " where " + " and ".join(where)
        sql += " order by sub.rank"

        try:
            rows = self.conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as exc:
            raise SearchError(
                f"FTS5 query failed for {query!r}: {exc}. The term is escaped before "
                f"use, so this usually indicates a malformed query construct."
            ) from exc
        hits = [
            CorpusHit(
                record_id=row[0], layer=row[1], edition_id=row[2],
                reference_display=row[3],
                # The STORED text, never the indexed form.
                text=row[4] if row[4] is not None else "",
                rank=float(row[5]),
                source_uri=row[6],
                verification_status=None,  # dataset-level, not per corpus record
                non_authoritative=(row[1] == "ai_hypothesis"),
            )
            for row in rows
        ]
        return tuple(self._dedupe_corpus(hits)[:limit])

    def search_claims(
        self, query: str, *, limit: int = 50, layers: Iterable[Any] | None = None,
        exclude_ai_hypothesis: bool = False, prefix: bool = False,
        diacritics: str = "both",
    ) -> tuple[ClaimHit, ...]:
        """Search the claim index.

        Args:
            exclude_ai_hypothesis: When True, ``ai_hypothesis`` claims are excluded even
                if the layer filter would admit them. Provided so that a query for
                sourced claims cannot accidentally include inference.
            diacritics: ``both`` (default), ``exact``, or ``folded``.
        """
        self.require_available()
        if limit < 1:
            raise SearchError(f"limit must be at least 1, got {limit}.")
        _validate_diacritic_mode(diacritics)
        match = self._claim_match(query, prefix, diacritics)

        # Same pagination rule as search_corpus: fetch all candidates, filter,
        # dedupe, then limit. Filters live outside the FTS MATCH subquery.
        inner = (
            "select claim_id, layer, non_authoritative, bm25(claim_fts) as rank "
            "from claim_fts where (claim_fts match ?) order by rank"
        )
        sql = (
            "select sub.claim_id, sub.layer, sub.non_authoritative, c.statement, "
            "sub.rank, c.source_uri, c.verification_state from (" + inner + ") as sub "
            "left join claims c on c.id = sub.claim_id"
        )
        params: list[Any] = [match]
        where: list[str] = []
        allowed = self._resolve_layers(layers)
        if allowed is not None:
            placeholders = ",".join("?" * len(allowed))
            where.append(f"sub.layer in ({placeholders})")
            params.extend(allowed)
        if exclude_ai_hypothesis:
            where.append("sub.layer <> 'ai_hypothesis'")
        if where:
            sql += " where " + " and ".join(where)
        sql += " order by sub.rank"

        try:
            rows = self.conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as exc:
            raise SearchError(f"FTS5 query failed for {query!r}: {exc}") from exc
        hits = [
            ClaimHit(
                claim_id=row[0], layer=row[1], non_authoritative=bool(row[2]),
                statement=row[3] if row[3] is not None else "",
                rank=float(row[4]),
                source_uri=row[5],
                verification_status=row[6],
            )
            for row in rows
        ]
        return tuple(self._dedupe_claims(hits)[:limit])

    def _term(self, folded: bool, query: str, prefix: bool) -> str:
        """Build the MATCH term for *query*.

        When matching the folded column (*folded* is True), the query is folded with
        the same NFD transform used at index time. When matching the original column
        it is used as written. Prefix matching operates on whole tokens, so the
        transform must be identical on both sides.
        """
        term = fold_diacritics(query) if folded else query
        return prefix_query(term) if prefix else phrase_query(term)

    def _corpus_match(self, query: str, prefix: bool, diacritics: str) -> str:
        """MATCH over the original and folded corpus columns.

        When ``diacritics`` is ``both`` the query is evaluated against BOTH columns
        and the hits are unioned. Searching only whichever column the query string
        happens to resemble would miss records stored in the other form (for
        example an unpointed Hebrew query against pointed storage), because FTS5
        ``unicode61 remove_diacritics 2`` does not normalize Greek or Hebrew.
        """
        if diacritics == "exact":
            return "{text} : " + self._term(False, query, prefix)
        if diacritics == "folded":
            return "{text_folded} : " + self._term(True, query, prefix)
        exact = "{text} : " + self._term(False, query, prefix)
        folded = "{text_folded} : " + self._term(True, query, prefix)
        return exact + " OR " + folded

    def _claim_match(self, query: str, prefix: bool, diacritics: str) -> str:
        """MATCH over the original and folded claim columns.

        When ``diacritics`` is ``both`` the query is evaluated against BOTH columns
        and the hits are unioned.
        """
        if diacritics == "exact":
            return "{statement} : " + self._term(False, query, prefix)
        if diacritics == "folded":
            return "{statement_folded} : " + self._term(True, query, prefix)
        exact = "{statement} : " + self._term(False, query, prefix)
        folded = "{statement_folded} : " + self._term(True, query, prefix)
        return exact + " OR " + folded

    @staticmethod
    def _dedupe_corpus(hits: list[CorpusHit]) -> list[CorpusHit]:
        """Deduplicate by record, keeping the best rank.

        A record can match on both columns; the union must not double-count it.
        """
        best: dict[str, CorpusHit] = {}
        for hit in hits:
            current = best.get(hit.record_id)
            if current is None or hit.rank < current.rank:
                best[hit.record_id] = hit
        return sorted(best.values(), key=lambda h: h.rank)

    @staticmethod
    def _dedupe_claims(hits: list[ClaimHit]) -> list[ClaimHit]:
        best: dict[str, ClaimHit] = {}
        for hit in hits:
            current = best.get(hit.claim_id)
            if current is None or hit.rank < current.rank:
                best[hit.claim_id] = hit
        return sorted(best.values(), key=lambda h: h.rank)

    def _resolve_layers(self, layers: Iterable[Any] | None) -> tuple[str, ...] | None:
        if layers is None:
            return None
        resolved = tuple(sorted({coerce_layer(layer).value for layer in layers}))
        if not resolved:
            raise SearchError(
                "A layer filter was supplied but was empty. Pass None to search all "
                "layers explicitly, or name at least one layer."
            )
        return resolved

    # ------------------------------------------------------------------ counts ----

    def corpus_index_size(self) -> int:
        self.require_available()
        return int(self.conn.execute("select count(*) from corpus_fts").fetchone()[0])

    def claim_index_size(self) -> int:
        self.require_available()
        return int(self.conn.execute("select count(*) from claim_fts").fetchone()[0])
