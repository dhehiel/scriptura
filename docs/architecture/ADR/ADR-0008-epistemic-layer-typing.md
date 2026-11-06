# ADR-0008 — Epistemic layer typing as a storage invariant

| Field | Value |
|---|---|
| **ID** | ADR-0008 |
| **Status** | **superseded** by [ADR-0011](ADR-0011-seven-layer-epistemic-model.md) |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-DATA-001 §2, §6; all modules; all outputs |
| **Supersedes** | — |
| **Superseded by** | ADR-0011 — Seven-Layer Epistemic Model and Removal of Universal Ranking |

> **Supersession note.** ADR-0011 supersedes this record: the layer set is expanded from five to seven values,
> and the universal ranking (`LAYER_ORDER`, `layer_strength`, `weakest_layer`, `compose_layer`) introduced here
> is removed. This document is retained unchanged as history. The storage-invariant principle it establishes
> (layer typing enforced by SQL `CHECK` constraints) remains in force and is carried forward into ADR-0011.

## Context

Biblical research data comes in radically different epistemic kinds. A manuscript reading, an archaeological
date, a morphological parse, a patristic interpretation, and a machine-generated hypothesis have different
authorities, different failure modes, and different obligations.

The dominant failure mode in biblical computing is that these are stored undifferentiated. Once flattened, they
become indistinguishable at query time — and a model's guess acquires the rhetorical weight of a manuscript
reading simply by appearing in the same result set.

The obvious mitigation is a convention: a `type` column that application code populates correctly. Conventions
fail. They are bypassed by a new code path, by a migration script, by a direct SQL client, by a contributor who
did not read the documentation, and by an agent optimising for a completed task.

## Decision

**Epistemic layer typing is a storage-level invariant, enforced by SQL `CHECK` constraints.**

Specifically:

1. The layer set is **closed**: `scripture`, `historical_evidence`, `linguistic_observation`,
   `theological_interpretation`, `ai_hypothesis`. Adding a layer requires an accepted ADR.
2. `layer` is `NOT NULL` with a `CHECK (layer IN (...))` constraint on every claim-bearing table.
3. Per-layer requirements are enforced by `CHECK` constraints:
   - `theological_interpretation` requires a non-empty `tradition` or `author`.
   - `scripture` requires `edition_id` and `reference_id`.
   - `ai_hypothesis` requires `model`, `method`, `inputs_json`, `confidence`, and `generated_at`.
   - `linguistic_observation` requires `source_dataset` or `analyst`.
   - `historical_evidence` requires `evidence_type`.
4. `ai_hypothesis` records carry `non_authoritative = 1`, enforced by
   `CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1)`.
5. `confidence`, where present, is constrained to `[0.0, 1.0]`.
6. Graph edges carry the same constraints (ADR-0007).
7. Layer promotion is recorded in `provenance_events` with `from_layer`, `to_layer`, `evidence`, `reasoning`,
   and `actor` — enforced by a `CHECK` constraint that rejects a promotion without them.
8. There is **no default layer**. A record inserted without a layer is rejected.
9. Layer survives serialisation, deserialisation, and the Gomine exchange boundary.

## Rationale

1. **Make the harmful state unrepresentable.** If an unattributed interpretation cannot be inserted, it does not
   need to be detected.
2. **Constraints cannot be bypassed.** A `CHECK` constraint holds against every code path, every script, and
   every direct SQL client. Application-level validation does not.
3. **No silent defaults.** A defaulted layer is a guessed layer. Guessing here is a source-integrity violation.
4. **The flag is structural.** Making `non_authoritative` a storage constraint means an unflagged AI hypothesis
   cannot exist, rather than relying on every presentation layer remembering to flag it.
5. **Promotion is auditable by construction.** A promotion without evidence and a decision-maker cannot be
   recorded.
6. **Closed set prevents drift.** An open layer vocabulary would accumulate ad-hoc values that erode the
   distinction the model exists to preserve.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **A `type` column populated by convention** | Bypassable by any code path, script, or SQL client. This is the failure mode the project exists to prevent. |
| **Application-level validation only** | Necessary but not sufficient. Kept as a first line of defence, with better error messages, but not relied upon alone. |
| **Separate tables per layer** | Strongly typed and attractive, but makes cross-layer queries require unions across five tables, and makes a mixed-layer result set awkward. Rejected for query ergonomics; the `CHECK` approach achieves the same enforcement in one table. |
| **An open layer vocabulary** | Would accumulate ad-hoc values and erode the distinction. |
| **Three layers instead of five** | Collapsing `historical_evidence` into `scripture`, or `linguistic_observation` into `scripture`, is precisely the error the model exists to prevent. |
| **Seven or more layers** | Premature. Five cover the distinctions that matter. The set can be extended by ADR when a genuine sixth kind is demonstrated. |

## Consequences

### Positive

- Unattributed interpretation, unflagged AI output, and layer-less records are **unrepresentable**.
- Promotion is auditable by construction.
- Mixed-layer result sets must visibly distinguish layers, because the data says so.
- The invariant holds against every access path.

### Negative

- `CHECK` constraint violations produce SQL-level errors that are less friendly than application errors.
  Mitigated: application validation runs first and produces specific messages; the constraint is the backstop.
- The wide `claims` table has many nullable layer-specific columns. Accepted: the alternative (five tables)
  costs more in query ergonomics than this costs in tidiness.
- Adding a layer requires a migration and an ADR. That friction is intentional.

### Neutral

- `non_authoritative` is stored rather than derived, so it travels with the record through every boundary.

## Compliance

| Document | Effect |
|---|---|
| `docs/architecture/BKB-DATA-001-data-model.md` | §2 layers; §6.3 SQL enforcement |
| `.clinerules/020-epistemic-layers.md` | Invariants L1–L10 |
| `NOTICE` | §5 the five layers |
| `AGENTS.md` | §2 layer discipline |
| `src/scriptura/core/layers.py` | Enum and validation |
| `src/scriptura/storage/migrations/0001_bootstrap.sql` | Constraints |
| `tests/test_layers.py`, `tests/test_storage.py` | Enforcement |

## Verification

| Check | Command |
|---|---|
| Closed set; unknown layer rejected | `python -m unittest tests.test_layers` |
| Unattributed interpretation rejected | `python -m unittest tests.test_layers` |
| Unflagged `ai_hypothesis` rejected | `python -m unittest tests.test_layers` |
| Scripture without edition rejected | `python -m unittest tests.test_layers` |
| Storage constraint rejects layer-less insert | `python -m unittest tests.test_storage` |
| Promotion without evidence rejected | `python -m unittest tests.test_storage` |
| Layer survives serialisation | `python -m unittest tests.test_serialisation` |
| `ai_hypothesis` edge flagged | `python -m unittest tests.test_graph` |

## Related

ADR-0007, BKB-DATA-001, BKB-VERIFY-001, DKF-ARCH-001, .clinerules/020

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
