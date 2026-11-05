# ADR-0010 — Licence gate on all corpus ingestion

| Field | Value |
|---|---|
| **ID** | ADR-0010 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-CORPUS-001 §4; src/scriptura/provenance/, src/scriptura/ingestion/ |
| **Supersedes** | — |

## Context

Ingestion is the point at which Scriptura takes on **legal responsibility** for someone else's data. A licensing
error here is not a bug; it is exposure for the project and for every downstream user.

Two verified facts shape this decision:

1. **Licensing is dataset-specific.** There is no blanket licence for biblical data. Several aggregators that
   Scriptura intends to evaluate are explicitly licensed **per item**, and at least one states plainly that each
   text is licensed separately and there is no overall licence for the collection. An aggregator-level licence
   therefore establishes nothing about any individual text.
2. **Licences differ in ways that matter mechanically.** Some are permissive with attribution (CC BY 4.0), some
   are share-alike (CC BY-SA 4.0), some are non-commercial (CC BY-NC 4.0), some are public-domain dedications,
   and some are all-rights-reserved. Composite datasets are frequently licensed in **layers**: the underlying
   text under one licence and the added annotation under another.

A licence check performed by a human reading documentation will eventually be skipped under time pressure. A
licence check performed by code cannot be.

## Decision

**All corpus ingestion passes through a licence gate that raises on failure.**

Specifically:

1. The gate lives in `src/scriptura/provenance/`, **not** in `src/scriptura/ingestion/`. A gate inside the thing
   it gates is not a gate.
2. The gate is evaluated **before** any network retrieval.
3. The gate evaluates ten conditions (BKB-CORPUS-001 §4.1, G1–G10), including: registry entry present, manifest
   entry present, `verification_status == verified`, primary-source licence with URL and retrieval date,
   verbatim attribution recorded, derivative and commercial status recorded, share-alike status recorded,
   milestone gate open, and per-dataset human authorisation.
4. The gate **raises** on failure. It never warns and continues.
5. The failure message names **every** unmet condition, not just the first.
6. The gate **cannot be bypassed** by configuration, environment variable, command-line flag, or code path.
7. The gate is **re-evaluated on every attempt**. A cached permission is not a permission.
8. Every gate evaluation is recorded, whether it permitted or refused.
9. `verification_status` values other than `verified` — `unverified`, `disputed`, `restricted`, `absent` — block
   ingestion.
10. Share-alike and non-commercial consequences are attached to the dataset record and propagate to derived
    records.

## Rationale

1. **Legal exposure is not recoverable by a patch.** A code defect can be fixed; an unlicensed redistribution
   cannot be un-done.
2. **Per-item licensing defeats aggregator-level reasoning.** The gate forces item-level resolution.
3. **A gate that warns is not a gate.** Under time pressure a warning is dismissed. An exception is not.
4. **Naming every unmet condition** turns a refusal into an actionable checklist rather than a dead end.
5. **Separation from ingestion** means the gate cannot be refactored away by someone improving the pipeline.
6. **Re-evaluation** prevents a stale permission from authorising a later attempt after a licence changed.
7. **Recording refusals** creates an audit trail showing the project did consider and decline.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **Documentation-only licence policy** | Will be skipped under pressure. Provides no enforcement. |
| **A checklist in the pull request template** | Kept as a **complement**, not a substitute. A checklist is advisory. |
| **A gate that warns and continues** | Rejected. A warning is dismissible. |
| **A gate inside the ingestion module** | Rejected. Coupling the gate to the thing it gates makes it refactorable away. |
| **A gate that can be overridden by a flag** | Rejected. An override flag is a bypass. |
| **Trusting the upstream aggregator's licence** | Rejected. Verified: aggregators license per item, and at least one states there is no overall licence. |
| **Ingest first, verify licence later** | Rejected. Retrieval is the act that creates exposure. |

## Consequences

### Positive

- Unlicensed ingestion is structurally prevented, not merely discouraged.
- Per-item licence resolution is forced.
- Refusals are actionable and audited.
- Share-alike and non-commercial consequences propagate automatically.

### Negative

- Ingestion is slower to start. That friction is the point.
- Every dataset requires primary-source licence research before it can be used. Accepted: this is the cost of
  not creating legal exposure.
- Some genuinely useful datasets will be unusable. Accepted and recorded as `restricted`.

### Neutral

- The manifest becomes a governance artefact that is reviewed like code.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/050-data-licensing.md` | §3 the ingestion licence gate |
| `docs/architecture/BKB-CORPUS-001-corpus-ingestion.md` | §4 gate; §13 prohibitions |
| `docs/data/source-registry.json` | `verification_status` per source |
| `docs/data/licence-manifest.json` | Authoritative licence record |
| `src/scriptura/provenance/licensing.py` | Implementation |
| `tests/test_licensing.py` | Enforcement |
| `NOTICE` | §2 third-party corpus data |

## Verification

| Check | Command |
|---|---|
| Gate refuses `unverified` | `python -m unittest tests.test_licensing` |
| Gate refuses missing registry entry | `python -m unittest tests.test_licensing` |
| Gate refuses missing manifest entry | `python -m unittest tests.test_licensing` |
| Gate names every unmet condition | `python -m unittest tests.test_licensing` |
| Gate cannot be bypassed by flag | `python -m unittest tests.test_licensing` |
| Gate refuses when milestone gate closed | `python -m unittest tests.test_licensing` |
| Registry ↔ manifest consistency | `make check-licences` |
| Ingestion framework honours the gate | `python -m unittest tests.test_ingestion` |

## Related

ADR-0003, BKB-CORPUS-001, .clinerules/050

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
