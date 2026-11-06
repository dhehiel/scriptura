# Architecture Decision Records

An Architecture Decision Record (ADR) captures a decision that is hard to reverse, architecturally load-bearing,
a relaxation of a standing constraint, contested, or likely to be re-litigated.

> **A decision that is not written down did not happen.**

Protocol: [.clinerules/070-decision-log-protocol.md](../../../.clinerules/070-decision-log-protocol.md).
Template: [ADR-TEMPLATE.md](ADR-TEMPLATE.md).

---

## Index

| ID | Title | Status | Affects |
|---|---|---|---|
| [ADR-0001](ADR-0001-sqlite-as-primary-store.md) | SQLite as the primary store | Accepted | BKB-ARCH-001, BKB-DATA-001 |
| [ADR-0002](ADR-0002-stdlib-only-m0-runtime.md) | Stdlib-only runtime at M0 | Accepted | BKB-ARCH-001, all |
| [ADR-0003](ADR-0003-json-machine-readable-registries.md) | JSON for machine-readable registries | Accepted | BKB-CORPUS-001, data governance |
| [ADR-0004](ADR-0004-fastapi-adoption-gate.md) | FastAPI adoption gate | Accepted | BKB-ARCH-001 §8 |
| [ADR-0005](ADR-0005-no-graph-database.md) | No independent graph database | Accepted | BKB-ARCH-001 §5, DKF-ARCH-001 §10 |
| [ADR-0006](ADR-0006-leann-optional-retrieval.md) | LEANN as an optional retrieval adapter | Accepted | BKB-ARCH-001 §7 |
| [ADR-0007](ADR-0007-modular-knowledge-graph.md) | Modular knowledge graph in SQLite | Accepted | BKB-DATA-001 §6, DKF-ARCH-001 §10 |
| [ADR-0008](ADR-0008-epistemic-layer-typing.md) | Epistemic layer typing as a storage invariant | **superseded** by ADR-0011 | BKB-DATA-001 §2, all |
| [ADR-0009](ADR-0009-fts5-primary-lexical-search.md) | SQLite FTS5 as primary lexical search | Accepted | BKB-ARCH-001 §7 |
| [ADR-0010](ADR-0010-licence-gate.md) | Licence gate on all corpus ingestion | Accepted | BKB-CORPUS-001 §4 |
| [ADR-0011](ADR-0011-seven-layer-epistemic-model.md) | Seven-layer epistemic model; removal of universal ranking | **proposed** | .clinerules/020, BKB-DATA-001, all layer consumers |

Numbering is sequential and **never reused**, even for a rejected or retired ADR.

---

## Statuses

| Status | Meaning |
|---|---|
| `proposed` | Drafted, under discussion |
| `accepted` | Approved by the maintainer; binding |
| `rejected` | Not approved; reasons recorded; retained |
| `deferred` | Not decided now; revisit conditions recorded |
| `superseded` | Replaced by a later ADR, which is named |
| `deprecated` | No longer applies; not replaced |

An ADR is never deleted and never silently edited after acceptance. Correction is by supersession.

---

## How to propose one

1. Open an issue using the
   [architecture decision template](../../../.github/ISSUE_TEMPLATE/architecture_decision.yml), stating the
   **problem**.
2. Copy [ADR-TEMPLATE.md](ADR-TEMPLATE.md) to `ADR-NNNN-short-kebab-title.md` with the next number.
3. Complete every section. **"Alternatives considered" is mandatory** — an ADR without it is incomplete.
4. Set status `proposed` and add it to the index above.
5. Request maintainer review.

On acceptance, the affected specifications are revised in the same change or a follow-up, and their
`Change history` references the ADR.
