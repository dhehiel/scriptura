# Governance

Scriptura is an open-source project. This document defines decision rights, change control, and roles.

---

## Principles

1. **Architecture precedes implementation.** A change to how Scriptura thinks requires an accepted decision
   record before code exists.
2. **Provenance precedes capability.** Where a choice trades provenance for function, provenance wins.
3. **Explicit beats implicit.** Defaults, assumptions, and silent inference are defects in this domain.
4. **Written beats remembered.** Decisions that are not written down did not happen.
5. **Disagreement is data.** Contested positions are recorded with their sources, not resolved by vote.
6. **Reversibility shapes scrutiny.** Easily reversed decisions move fast; hard-to-reverse decisions require an ADR.

---

## Roles

| Role | Responsibility |
|---|---|
| **Maintainer** | Final decision authority. Approves ADRs, schema changes, specification changes, licence determinations, and milestone gates. May merge to `main`. |
| **Committer** | Reviews and merges contributions within an approved area. May not approve ADRs, specification changes, or licence determinations. |
| **Contributor** | Anyone submitting issues, documentation, or code. |
| **Reviewer** | A domain expert consulted on scripture, linguistics, history, theology, or licensing. Advisory; not a merge gate. |
| **User** | Anyone deploying Scriptura. Feedback is welcomed through issues. |

Roles are earned by sustained, reviewed contribution and are recorded here. At M0 the project has a single
maintainer; this document will be updated as committers are added.

**Single-maintainer caveat.** A single maintainer is a governance risk, not a strength. Recruiting at least one
additional maintainer with domain expertise is a stated objective before M1 opens. Until then, decisions that
would normally require a second approver are recorded as *provisional* and revisited when a second maintainer
exists.

---

## Decision rights

| Decision | Authority | Mechanism |
|---|---|---|
| Bug fix, documentation wording, tests | Committer | Pull request review |
| New module within an approved area | Committer | Pull request review |
| New mandatory dependency | Maintainer | Accepted ADR |
| New optional dependency | Committer | Pull request + ADR note |
| HTTP surface change | Maintainer | Accepted ADR |
| New service, broker, or graph database | Maintainer | Accepted ADR, with demonstrated insufficiency of SQLite |
| Schema or migration change | Maintainer | Pull request + maintainer approval |
| Architecture specification change | Maintainer | Accepted ADR + specification revision |
| **Licence determination for a dataset** | Maintainer | Primary-source evidence recorded in the licence manifest |
| **Milestone gate opening** | Maintainer | Explicit written approval in the milestone document |
| **Corpus ingestion of any dataset** | Maintainer | Licence `verified` + gate open + human authorisation per dataset |
| Epistemic layer promotion | Maintainer | Recorded decision with evidence; append-only audit |
| Removal of provenance-bearing data | Maintainer | Recorded decision; append-only audit |

Decisions requiring maintainer authority cannot be delegated to an automated agent.

---

## Specification change control

The six foundational specifications are normative. Changing one is a governance act.

**Process:**

1. Open an issue using the architecture decision template, stating the problem, not the preferred solution.
2. Draft an ADR under `docs/architecture/ADR/` with status `proposed`.
3. Discuss on the issue. Domain reviewers are consulted where the change touches scripture, language, history,
   theology, or licensing.
4. Maintainer sets status to `accepted`, `rejected`, or `deferred`, with reasons recorded.
5. On acceptance, the affected specification is revised: its `Status` and `Change history` are updated, and the
   revision references the ADR.
6. Implementation follows the accepted specification, never precedes it.

**Specification statuses:** `draft`, `proposed`, `accepted`, `superseded`, `deprecated`.

An accepted specification may only be `superseded` by another accepted specification. It is never silently
edited. Where a specification and an implementation disagree, the specification is authoritative and the
implementation is a bug.

---

## Milestone gating

Milestones are gated, not scheduled. A milestone opens only when its predecessor's exit criteria are met and
the maintainer records that they are.

**M0 → M1 gate requires:**

- M0 acceptance criteria met and recorded in
  [docs/milestones/M0-acceptance-criteria.md](docs/milestones/M0-acceptance-criteria.md).
- **Architecture review completed.** This is an explicit human review of the six specifications, recorded with
  reviewer identity and date. It is not satisfiable by an agent or by CI.
- Licence manifest and source registry validated, with every ingestion candidate either `verified` or explicitly
  excluded.
- No corpus data present, confirmed by `make check`.

Until the gate opens, ingestion work is out of scope regardless of how ready the code appears. See
[BKB-CORPUS-001](docs/architecture/BKB-CORPUS-001-corpus-ingestion.md).

---

## Branching and release

- `main` is the only long-lived branch and is always releasable.
- Work happens on short-lived branches from `main`.
- Protected: no force-push to `main`; no direct push without review.
- Releases are tagged `vMAJOR.MINOR.PATCH` and recorded in [CHANGELOG.md](CHANGELOG.md).
- Milestone snapshots are tagged `m0`, `m1`, and so on.

Semantic versioning applies to the code and the schemas. Specification revisions are versioned within their own
documents and cross-referenced from the changelog.

---

## Conflict resolution

1. Discuss on the issue or pull request.
2. Where the dispute is about facts — what a source says, what a licence permits, what a manuscript reads —
   resolve it by producing the primary source. Facts are not voted on.
3. Where the dispute is about judgement and cannot be resolved by evidence, the maintainer decides and records
   the reasoning in the ADR or the pull request.
4. Where the dispute is about doctrine or canon, Scriptura does not decide. Both positions are recorded with
   their attributions, and the disagreement is preserved in the data.

A dissenting position that is well-sourced is recorded in the ADR even when the decision goes against it.

---

## Transparency

- All decisions of consequence are recorded publicly: in an ADR, a milestone document, an issue, or the
  changelog.
- Private deliberation is limited to security and data-integrity incidents, per [SECURITY.md](SECURITY.md).
- Meeting notes, if any, are published.

---

## Related documents

- [README.md](README.md) — project overview
- [AGENTS.md](AGENTS.md) — binding agent obligations
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution process
- [SECURITY.md](SECURITY.md) — vulnerability and integrity reporting
- [.clinerules/000-project-governance.md](.clinerules/000-project-governance.md) — persistent governance rules
- [.clinerules/070-decision-log-protocol.md](.clinerules/070-decision-log-protocol.md) — ADR protocol
- [docs/architecture/ADR/README.md](docs/architecture/ADR/README.md) — decision record index
