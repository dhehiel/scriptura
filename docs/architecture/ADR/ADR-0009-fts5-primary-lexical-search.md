# ADR-0009 — SQLite FTS5 as primary lexical search

| Field | Value |
|---|---|
| **ID** | ADR-0009 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §7; src/scriptura/search/ |
| **Supersedes** | — |

## Context

The dominant query patterns in biblical research are **lexical and morphological**: find every occurrence of a
lemma; find a form; find a phrase; find a word across a corpus; find a term regardless of accentuation.

Two properties are essential and non-negotiable for this domain:

1. **Diacritic handling.** Greek polytonic text carries breathings, accents, and iota subscripts. Hebrew carries
   pointing and cantillation. A search for a Greek word must succeed whether or not the user supplies accents,
   while the **stored text** must remain exactly as the edition attests it.
2. **Co-location with data.** An index in a separate system creates a synchronisation problem: which is
   authoritative, and what happens when they disagree?

Verified platform capability: SQLite 3.40.1 with `ENABLE_FTS5` present, JSON1 functional, and the `unicode61`
tokenizer supporting `remove_diacritics 2`. Confirmed by direct probe in the reference environment.

## Decision

**SQLite FTS5 is the primary lexical search tier and is always available.**

Specifically:

1. FTS5 virtual tables index corpus text and claim statements.
2. Tokenization uses `unicode61` with `remove_diacritics 2` for matching.
3. **Diacritic folding is a search affordance only.** The stored text is never altered. BKB-DATA-001 §7 rule U6.
4. FTS5 tables are maintained in the same database file as the data they index.
5. Index maintenance is transactional with the write that changes the indexed content.
6. Search results always carry epistemic layer information.
7. Search results identify the edition or dataset they came from.
8. A search never silently merges layers. Layer filtering is a first-class parameter.
9. FTS5 is the baseline tier; semantic retrieval (ADR-0006) is optional and complementary, never substitutive.
10. Where an external-content FTS5 table is used, the content table is authoritative and the index is
    reconstructible from it.

## Rationale

1. **No synchronisation problem.** Index and data are one transactional store.
2. **Diacritic folding without text mutation.** `remove_diacritics 2` gives accent-insensitive matching while the
   stored text stays exact. This is precisely the requirement.
3. **In-database.** No second process, no second index format, no second failure mode.
4. **Verified available.** Confirmed by probe, not assumed.
5. **Ranking built in.** `bm25()` ranking is available without additional machinery.
6. **Prefix and phrase queries** cover the common philological patterns.
7. **Zero additional dependency.** Consistent with ADR-0002.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **Elasticsearch / OpenSearch** | A server cluster, a JVM, and a second store with a synchronisation problem. Enormous operational burden for a bounded corpus. |
| **Lucene directly** | Same objection, plus a JVM dependency. |
| **Tantivy / Whoosh** | Whoosh is unmaintained. Tantivy requires a Rust binding, contrary to ADR-0002. |
| **PostgreSQL full-text search** | ADR-0001 already rejected PostgreSQL. |
| **SQLite FTS4** | Superseded by FTS5: better ranking (`bm25`), better tokenizer options, better performance. |
| **LIKE-based scanning** | No index, no ranking, no phrase semantics, and O(n) per query. Unusable at corpus scale. |
| **Trigram index** | Useful for fuzzy matching and worth revisiting as a **complement** for orthographic-variant search. Not a substitute for lexical search. |

## Consequences

### Positive

- Accent-insensitive search over polytonic Greek and pointed Hebrew without altering stored text.
- One transactional store; no synchronisation problem.
- `bm25` ranking, phrase queries, and prefix queries available.
- No additional dependency or process.

### Negative

- FTS5 tokenization is not linguistically aware. It does not lemmatise. Mitigated: lemmatisation is a
  `linguistic_observation` dataset concern, indexed separately, not a tokenizer concern.
- Right-to-left and bidirectional text handling depends on `unicode61` behaviour and must be tested per script
  once real data exists. Recorded as an open question.
- No built-in fuzzy matching. Mitigated: revisit with a trigram complement if required.
- Hebrew morphology (prefixes and suffixes) is not handled by tokenization. Mitigated: morphological datasets
  provide segmented forms, indexed as separate fields.

### Neutral

- Index size adds to the database file. Accepted.

## Open questions

1. Which tokenizer configuration best serves Hebrew, given prefix and suffix clitics? Requires real data.
2. Is a trigram complement warranted for orthographic-variant search?
3. How should cantillation marks be treated for matching versus display?

All three require corpus data and are therefore deferred past M0.

## Compliance

| Document | Effect |
|---|---|
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §7 retrieval architecture |
| `docs/architecture/BKB-DATA-001-data-model.md` | §7 rule U6 |
| `.clinerules/040-engineering.md` | §1 baseline table |
| `src/scriptura/search/fts.py` | Implementation |
| `tests/test_fts.py` | Enforcement |

## Verification

| Check | Command |
|---|---|
| FTS5 capability detected | `python -m unittest tests.test_storage` |
| Index creation and query | `python -m unittest tests.test_fts` |
| Diacritic-folded matching | `python -m unittest tests.test_fts` |
| Stored text not mutated by folding | `python -m unittest tests.test_fts` |
| Results carry layer information | `python -m unittest tests.test_fts` |
| Layer filtering | `python -m unittest tests.test_fts` |

## Related

ADR-0001, ADR-0002, ADR-0006, BKB-ARCH-001, BKB-DATA-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
