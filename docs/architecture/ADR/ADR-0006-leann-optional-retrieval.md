# ADR-0006 — LEANN as an optional retrieval adapter

| Field | Value |
|---|---|
| **ID** | ADR-0006 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §7; src/scriptura/retrieval/ |
| **Supersedes** | — |

## Context

Lexical search (ADR-0009) handles the dominant biblical query patterns: lemma, form, phrase, and diacritic-variant
matching. It does not handle **semantic** retrieval — finding passages that discuss a concept without sharing its
vocabulary.

The brief specifies an *optional* LEANN semantic retrieval adapter. LEANN is verified as: PyPI package `leann`,
current release 0.3.9 (published 2026-11-02), **MIT License**, requires Python >= 3.10, providing a vector index
with `hnsw`, `diskann`, and `ivf` backends and a `LeannBuilder` / `LeannSearcher` / `LeannChat` API. Its
published claim is a substantially smaller index footprint than conventional vector stores at comparable recall.

Two things must be noted honestly:

1. LEANN is **not installed** in the reference environment (no package-index access, per ADR-0002). Therefore
   its retrieval quality, index size, and recall characteristics are **not verified by this project**. The
   storage-efficiency claim is the vendor's, not ours.
2. A dependency that cannot be installed must not be load-bearing. If semantic retrieval were mandatory, the
   system could not be verified here.

## Decision

**LEANN is an optional retrieval adapter.** It is never mandatory, never load-bearing, and never assumed present.

Specifically:

1. `src/scriptura/retrieval/leann_adapter.py` imports LEANN behind a capability probe. Absence is a **degraded
   mode**, not an error.
2. SQLite FTS5 (ADR-0009) is the **baseline** retrieval tier and is always available.
3. The retrieval router probes capabilities at construction and selects a backend accordingly.
4. The router reports which backend served a request. Results from different backends are never silently mixed.
5. A caller may pin a backend. Pinning an unavailable backend **raises** rather than silently falling back.
6. Results always carry epistemic layer information regardless of backend.
7. No backend may reorder or filter results in a way that drops layer information.
8. Embedding generation is out of scope for the adapter contract at M0; an embedding source is a separate
   decision requiring its own ADR.
9. LEANN's index artefacts are local files under the operator's control and are never committed.

## Rationale

1. **Optional means optional.** A capability whose absence degrades functionality but never breaks correctness is
   the correct shape for a research tool used across heterogeneous environments.
2. **ADR-0002 compliance.** An uninstallable package cannot be mandatory.
3. **Honest verification.** This project cannot verify LEANN's performance claims. Making it load-bearing would
   mean building on an unverified foundation.
4. **MIT licence is compatible** with Apache 2.0, so optional adoption creates no licensing conflict.
5. **Separation of concerns.** Keeping `search` (always available) distinct from `retrieval` (optional) prevents
   an optional dependency from becoming structurally load-bearing.
6. **Reversibility.** The adapter can be removed without affecting correctness.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **LEANN as the primary retrieval backend** | Not installable in the reference environment; performance claims unverified by this project; would make correctness depend on an unverified third party. |
| **FAISS** | Heavier native dependency, larger install footprint, and the same objection applies: not installable here. |
| **hnswlib** | Same objection. |
| **sqlite-vec / sqlite-vss** | Attractive because it stays inside SQLite and would preserve single-file auditability. **Worth a future ADR** — it may be a better fit than LEANN for this project. Not adopted at M0 because it is a native extension with platform-specific build requirements, contrary to ADR-0002. |
| **No semantic retrieval at all** | Rejected. Semantic retrieval is genuinely valuable for concept search, and specifying the seam now costs little. |
| **A pluggable interface with no reference implementation** | Rejected. A seam with no implementation is untested. The LEANN adapter is the reference implementation of the seam, even though it is inert here. |

## Consequences

### Positive

- Semantic retrieval is available to operators who install LEANN.
- Correctness never depends on it.
- The seam is defined and tested (via the degraded path), so another backend can be added later.
- No licence conflict.

### Negative

- Out of the box, Scriptura has lexical search only.
- Two retrieval code paths must be maintained.
- LEANN's actual performance in this domain is unknown until measured. Recorded as an open question.

### Neutral

- Operators who want semantic retrieval must install `leann` themselves and accept its own licence and
  dependencies.

## Open questions

Recorded honestly, not resolved:

1. What embedding model would serve biblical Greek, Hebrew, Latin, and English? Requires its own ADR.
2. Is `sqlite-vec` a better fit than LEANN, given ADR-0001's single-file auditability requirement?
3. What is LEANN's measured recall on biblical concept queries? Unmeasured.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/040-engineering.md` | §1 baseline table; §2 rule 3 |
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §7 retrieval architecture; principle P7 |
| `NOTICE` | §3 lists LEANN as optional, MIT |
| `src/scriptura/retrieval/leann_adapter.py` | Import-guarded adapter |
| `tests/test_retrieval.py` | Enforces graceful degradation |

## Verification

| Check | Command |
|---|---|
| Absence of LEANN does not break import | `python -m unittest tests.test_retrieval` |
| Router reports degraded mode | `python -m unittest tests.test_retrieval` |
| Pinning an unavailable backend raises | `python -m unittest tests.test_retrieval` |
| Results carry layer information | `python -m unittest tests.test_retrieval` |
| FTS5 baseline always available | `python -m unittest tests.test_fts` |

## Related

ADR-0002, ADR-0009, BKB-ARCH-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
