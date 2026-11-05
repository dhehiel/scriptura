# 000 — Project Governance

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

---

## 1. Mission

Scriptura is an open, extensible **Biblical Knowledge and Research Infrastructure**. It exists so that biblical
research questions can be asked against provenanced data, with kinds of claim auditably separated.

Scriptura is **infrastructure**. It is not a Bible app, not a devotional product, not a confessional statement,
and not an authority on scripture, history, language, or doctrine.

## 2. Scope

### In scope

- Structured, provenanced storage of scripture texts by **named edition**.
- Original-language analysis: morphology, syntax, lexicography.
- Historical and material context, as evidence distinct from scripture.
- Theological interpretation, as attributed positions distinct from fact.
- Cross-reference and cross-domain discovery, with hypotheses flagged as hypotheses.
- Verification: evidence chains, confidence, disagreement.
- Interoperability with Gomine at the boundary.

### Out of scope

- Adjudicating canon, doctrine, translation preference, or historicity.
- Producing devotional, catechetical, homiletic, or evangelistic content.
- Ranking traditions, denominations, or editions.
- Presenting machine inference as authority.
- Serving as a citation of record for anything. Scriptura points to sources; it is not the source.

## 3. Non-goals — standing constraints

These are permanent constraints, not milestone deferrals. Relaxing any of them requires an accepted ADR.

1. **No corpus ingestion before architecture review.** Ingestion is gated. See
   [050-data-licensing.md](050-data-licensing.md).
2. **No autonomous agents without explicit authorisation.** Agents are specified declaratively until
   [BKB-AGENTS-001](../docs/architecture/BKB-AGENTS-001-agent-framework.md) is implemented under human
   supervision at M5 or later.
3. **No microservices.** One process, one database file. Splitting a service requires an ADR demonstrating that
   a single process cannot satisfy the requirement.
4. **No independent graph database.** The knowledge graph is SQLite tables. See
   [ADR-0005](../docs/architecture/ADR/ADR-0005-no-graph-database.md).
5. **No unlicensed or unverified dataset.** See [050-data-licensing.md](050-data-licensing.md).
6. **No mandatory third-party runtime dependency** without an accepted ADR. See
   [040-engineering.md](040-engineering.md).
7. **No collapse of epistemic layers.** See [020-epistemic-layers.md](020-epistemic-layers.md).
8. **No runtime dependency on Gomine.** See [BKB-ARCH-001 §10](../docs/architecture/BKB-ARCH-001-system-architecture.md).

## 4. Decision rights

| Decision | Authority |
|---|---|
| Bug fix, documentation, tests | Committer |
| New module within an approved area | Committer |
| New mandatory or optional dependency | Maintainer (ADR) |
| HTTP surface change | Maintainer (ADR) |
| New service, broker, or graph database | Maintainer (ADR + demonstrated SQLite insufficiency) |
| Schema or migration change | Maintainer |
| Architecture specification change | Maintainer (ADR + specification revision) |
| Licence determination for a dataset | Maintainer (primary-source evidence) |
| Milestone gate opening | Maintainer (explicit written approval) |
| Corpus ingestion of any dataset | Maintainer (verified licence + open gate + per-dataset authorisation) |
| Epistemic layer promotion | Maintainer (recorded, append-only) |
| Removal of provenance-bearing data | Maintainer (recorded, append-only) |

Decisions requiring maintainer authority **cannot be delegated to an automated agent**. An agent may draft,
research, and recommend; it may not decide.

## 5. Milestone gating

Milestones are **gated, not scheduled**. A milestone opens only when its predecessor's exit criteria are met
**and** the maintainer records that they are met.

Gates are satisfied by evidence, not by assertion. Each criterion names the command or artefact that
demonstrates it. See [../docs/milestones/M0-acceptance-criteria.md](../docs/milestones/M0-acceptance-criteria.md).

**The M0 → M1 gate additionally requires a completed architecture review by a human reviewer, recorded with
identity and date.** This criterion cannot be satisfied by CI, by an agent, or by self-attestation.

Until a gate opens, work belonging to the next milestone is out of scope **regardless of how ready the code
appears**. Readiness is not authorisation.

## 6. Documentation obligations

Every milestone delivers documentation as a first-class artefact, not as an afterthought:

- The architecture specifications affected.
- The ADRs recording decisions taken.
- The changelog entry.
- The milestone criteria and their evidence.
- Updated dataset governance where datasets are involved.

A milestone whose documentation is incomplete is not complete.

## 7. Transparency

- Decisions of consequence are recorded publicly: ADR, milestone document, issue, or changelog.
- Private deliberation is limited to security and data-integrity incidents.
- A well-sourced dissenting position is recorded even when the decision goes against it.

## 8. Reporting honesty

No task may be reported complete unless it was **performed and verified**. Where work is partial, blocked, or
skipped, the report must say so precisely, naming what remains and why.

Claiming unperformed work is a release-blocking defect. See
[040-engineering.md](040-engineering.md) §9.

---

**Related:** [README.md](README.md) · [010-source-integrity.md](010-source-integrity.md) ·
[040-engineering.md](040-engineering.md) · [050-data-licensing.md](050-data-licensing.md) ·
[070-decision-log-protocol.md](070-decision-log-protocol.md) ·
[../GOVERNANCE.md](../GOVERNANCE.md)
