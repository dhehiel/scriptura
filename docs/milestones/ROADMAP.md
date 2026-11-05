# Milestone Plan

Scriptura's development plan. Milestones are **gated, not scheduled**.

> **A milestone opens only when its predecessor's exit criteria are met and the maintainer records that they
> are.** Dates are not gates. Readiness is not authorisation.

---

## Overview

| Milestone | Name | Scope | Gate to open | Status |
|---|---|---|---|---|
| **M0** | Architecture Foundation | Documentation, governance, schemas, storage core, verification harness. **No corpus data.** | — | Criteria A–H met; **architecture review outstanding** |
| **M1** | Provenanced Text Core | Reference core in production; first single-edition ingestion under full provenance | M0 architecture review + maintainer approval | Not started |
| **M2** | Witnesses and Language | Multi-witness alignment, variants, original-language morphology | M1 exit | Not started |
| **M3** | Graph and Discovery | Knowledge graph population; cross-reference discovery strategies | M2 exit | Not started |
| **M4** | Verification in Production | Verification checks implemented; evaluation benchmarks | M3 exit | Not started |
| **M5** | Supervised Agents | Research agents under explicit human authorisation | M4 exit + separate authorisation | Not started |

---

## M0 — Architecture Foundation

**Goal:** establish the architectural and governance foundation so that everything built afterwards is built
inside a containment structure rather than being contained after the fact.

**Delivered:** foundational documentation; `.clinerules/`; directory structure; the six architecture
specifications; ten ADRs; dataset source registry and licence manifest; technology architecture; JSON schemas;
storage, graph, search, retrieval, provenance, and ingestion-framework code; test suite; repository checkers.

**Explicitly not delivered:** corpus data; dataset adapters; executing agents; verification check
implementations; discovery strategy implementations.

**Exit:** [M0-acceptance-criteria.md](M0-acceptance-criteria.md). Criteria A–H are met with evidence.
**Criterion I1 — human architecture review — is not met**, so the gate remains closed.

---

## M1 — Provenanced Text Core

**Goal:** prove the data model against real data, with one edition, under complete provenance.

**Scope:**

1. Book registry and canon profiles populated and validated.
2. First dataset adapter implemented, for a **licence-cleared** source only.
3. Ingestion executed under the licence gate, with per-dataset human authorisation.
4. Full provenance capture: source URI, retrieval timestamp, content hash, licence reference.
5. FTS5 index populated and queryable.
6. Dataset manifest committed (metadata only).
7. Attribution propagated to `NOTICE`.

**Deliberately excluded:** multiple editions; variants; morphology; the knowledge graph; any agent.

**Why one edition first:** the data model's central claim is that a `scripture` record is always attributable
to a **named edition**. That claim is untested until one edition is actually ingested with full provenance.
Everything else depends on it.

**Gate to open:**

- M0 criterion I1 recorded: human architecture review, with identity and date.
- Maintainer approval of the M0 → M1 gate.
- Target dataset `licence_cleared: true` **and** per-dataset human authorisation recorded.
- Ingestion gate opened in `docs/data/source-registry.json`.

**Candidate first datasets** (licence-cleared at M0, none authorised):

| Source | Licence | Consideration |
|---|---|---|
| `src-bsb` | Public domain dedication | Simplest licence; no attribution obligation; English only |
| `src-oshb` | CC BY 4.0 | Mandatory verbatim attribution; Hebrew with morphology |
| `src-sblgnt` | CC BY 4.0 | Attribution wording still to be confirmed |

`src-etcbc-bhsa` is licence-cleared but **non-commercial**, so it requires quarantine and is a poorer first
candidate. `src-stepbible-data` is licence-cleared but its CC BY 4.0 does not cover embedded modern
translations, so individual datasets within it need separate verification.

---

## M2 — Witnesses and Language

**Goal:** represent the fact that scripture exists as multiple witnesses, and that language is analysed rather
than given.

**Scope:**

1. Multiple editions of the same text, with edition-level provenance.
2. Witnesses (manuscripts, versions) and witness-level readings.
3. Variant apparatus as **recorded variants, never resolutions**.
4. Morphological and lexicographic datasets as `linguistic_observation` records, with competing analyses
   preserved.
5. Cross-edition reference mapping, recording numbering divergence rather than forcing it.
6. Non-commercial quarantine implemented end to end, if any NC dataset is ingested.

**Gate to open:** M1 exit criteria met and recorded.

---

## M3 — Graph and Discovery

**Goal:** make the knowledge base a knowledge **graph**, and begin proposing relationships.

**Scope:**

1. Node and relation vocabularies registered and populated.
2. Graph populated from sourced relationships only.
3. Discovery strategy implementations, emitting `ai_hypothesis` records exclusively.
4. Hypothesis lifecycle state machine.
5. Salience ranking, with refuted and dismissed hypotheses suppressed.
6. Bounded, layer-filtered traversal in production use.
7. Optional semantic retrieval exercised end to end, if an operator installs it.

**Gate to open:** M2 exit criteria met and recorded.

**Invariant:** every discovery output is `ai_hypothesis` and flagged. Layer and flag integrity must be 100%,
and anything less is a blocking defect (DKF-ARCH-001 §9, EV5).

---

## M4 — Verification in Production

**Goal:** distinguish what Scriptura has verified from what it has merely collected.

**Scope:**

1. The baseline verification check set implemented (BKB-VERIFY-001 §7.2).
2. Evidence chains stored and queryable.
3. Confidence derived from chains, never asserted.
4. Verification states assigned and audited.
5. Evaluation benchmarks, versioned and provenanced, with their own licensing.
6. Per-case evaluation reporting, including refutation rates.

**Gate to open:** M3 exit criteria met and recorded.

---

## M5 — Supervised Agents

**Goal:** allow agents to assist research, inside containment.

**Scope:**

1. Agent runtime implementing BKB-AGENTS-001, **deny-by-default**.
2. Agent specifications approved individually by the maintainer.
3. Scope, volume, cost, and iteration limits enforced.
4. Audit logging of every run.
5. Human review points enforced.
6. Kill switch.

**Gate to open:** M4 exit criteria met and recorded, **plus separate explicit maintainer authorisation**.

**Non-grantable capabilities remain non-grantable** at M5 and forever: writing to any layer other than
`ai_hypothesis`, promoting a layer, mutating provenance, ingesting, retrieving, determining a licence,
executing code, opening a gate, self-approval.

---

## Standing constraints across all milestones

These do not lapse when a milestone opens. Relaxing any requires an accepted ADR.

| # | Constraint |
|---|---|
| 1 | No corpus bytes committed to version control, ever |
| 2 | No ingestion without a `verified` licence, an open gate, and per-dataset human authorisation |
| 3 | No collapse of the five epistemic layers |
| 4 | No unflagged `ai_hypothesis` output |
| 5 | No unattributed `theological_interpretation` |
| 6 | No generated scripture text |
| 7 | No microservices, brokers, or worker pools |
| 8 | No independent graph database |
| 9 | No mandatory third-party runtime dependency without an ADR |
| 10 | No runtime dependency on Gomine |
| 11 | No runtime network I/O |
| 12 | No task reported complete that was not performed and verified |

---

## What this plan deliberately does not contain

- **Dates.** Milestones are gated on evidence, not on a calendar.
- **Feature commitments beyond the next milestone.** Later milestones are directional; their scope is revised
  at each gate based on what the previous milestone actually revealed.
- **A promise of autonomous agents.** M5 is conditional and may be deferred indefinitely.
- **A promise of any particular dataset.** Dataset availability and licensing are determined per dataset, and
  a dataset that cannot be licensed is simply not used.

---

## Related

- [M0-acceptance-criteria.md](M0-acceptance-criteria.md)
- [README.md](README.md)
- [../architecture/README.md](../architecture/README.md)
- [../data/README.md](../data/README.md)
- [../../GOVERNANCE.md](../../GOVERNANCE.md)
- [../../.clinerules/000-project-governance.md](../../.clinerules/000-project-governance.md)
