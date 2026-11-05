# 070 — Decision Log Protocol

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

> **A decision that is not written down did not happen.**

---

## 1. What requires a decision record

An Architecture Decision Record (ADR) is required for any decision that is:

- **hard to reverse** (storage engine, identifier scheme, data model, serialisation format), or
- **architecturally load-bearing** (module boundaries, process model, dependency policy), or
- **a relaxation of a standing constraint** (non-goals in
  [000-project-governance.md](000-project-governance.md)), or
- **contested** (reasonable people disagreed), or
- **likely to be re-litigated** by a future contributor who does not know why it was decided.

Decisions that are trivially reversible and uncontested do not need an ADR. They need a pull request.

## 2. ADR location and numbering

- Location: `docs/architecture/ADR/`
- Filename: `ADR-NNNN-short-kebab-title.md`
- Numbering: sequential, zero-padded to four digits, **never reused**, even for a rejected or retired ADR.
- Index: `docs/architecture/ADR/README.md`, updated in the same change.

## 3. ADR statuses

| Status | Meaning |
|---|---|
| `proposed` | Drafted, under discussion |
| `accepted` | Approved by the maintainer; binding |
| `rejected` | Not approved; reasons recorded; retained for the record |
| `deferred` | Not decided now; revisit conditions recorded |
| `superseded` | Replaced by a later ADR, which is named |
| `deprecated` | No longer applies; not replaced |

An ADR is never deleted and never silently edited after acceptance. Correction is by supersession.

## 4. ADR structure

Every ADR contains, in order:

1. **ID and title.**
2. **Status** and date.
3. **Context.** The problem, the constraints, the forces. Facts, with sources.
4. **Decision.** What was decided, stated declaratively and unambiguously.
5. **Rationale.** Why this and not the alternatives.
6. **Alternatives considered.** Each with the reason it was not chosen. **This section is mandatory.** An ADR
   with no alternatives considered is incomplete.
7. **Consequences.** Positive, negative, and neutral. What becomes easier, harder, and impossible.
8. **Compliance.** Which `.clinerules/` and specifications this affects.
9. **Verification.** How conformance is checked, and by what command or test.
10. **Related records.** ADRs, specifications, issues.
11. **Change history.**

Template: `docs/architecture/ADR/ADR-TEMPLATE.md`.

## 5. Specification change control

The six foundational specifications are normative.

**Process:**

1. Open an issue stating the **problem**, not the preferred solution.
2. Draft an ADR with status `proposed`.
3. Discuss. Consult domain reviewers where the change touches scripture, language, history, theology, or
   licensing.
4. Maintainer sets `accepted`, `rejected`, or `deferred`, with reasons recorded.
5. On acceptance, revise the affected specification: update `Status` and `Change history`, reference the ADR.
6. Implementation **follows** the accepted specification. It never precedes it.

**Specification statuses:** `draft`, `proposed`, `accepted`, `superseded`, `deprecated`.

An accepted specification may be `superseded` only by another accepted specification. It is never silently
edited.

**Where a specification and an implementation disagree, the specification is authoritative and the
implementation is a bug.**

## 6. Rule change control

Changes to `.clinerules/` require:

1. An issue stating the problem the change addresses.
2. An ADR where the change relaxes any standing constraint.
3. Maintainer approval.
4. An update to `.clinerules/README.md` if the index changes.
5. A `CHANGELOG.md` entry.

A rule may be **tightened** by a committer with maintainer approval. A rule may be **relaxed** only by the
maintainer, with an ADR.

## 7. Milestone gate records

Opening a milestone gate is recorded in the milestone document with:

- the date
- the identity of the approver
- the per-criterion evidence, including commands run and their output
- any criteria waived, with reasons

A gate opened without a record is not open.

The M0 → M1 gate additionally requires a **completed architecture review by a human reviewer**, recorded with
identity and date. This cannot be satisfied by CI, by an agent, or by self-attestation.

## 8. Layer promotion records

Promoting content between epistemic layers is recorded, append-only, with:

- the record identifiers affected
- the source and target layers
- the **new evidence** that changes the warrant
- the decision-maker and date
- the reasoning

Relabelling without such a record is a Critical integrity incident.

## 9. Licence determination records

A licence determination is recorded in `docs/data/licence-manifest.json` with:

- the primary source URL
- the retrieval date
- the licence exactly as written
- the attribution string, verbatim
- derivative, commercial, and share-alike status

A determination without a primary source is not a determination.

## 10. Provenance correction records

Provenance is append-only. Correction is by appending a superseding record that names:

- the record superseded
- what was wrong
- what is correct
- the evidence
- the date and actor

Silent deletion or mutation of provenance is prohibited.

## 11. What does not need a record

- Typographical fixes.
- Test additions that do not change behaviour.
- Documentation clarifications that do not change a normative statement.
- Refactoring that preserves behaviour and public API.

If in doubt, write the record. An unnecessary record costs minutes; a missing one costs a re-litigation.

---

**Related:** [000-project-governance.md](000-project-governance.md) ·
[../GOVERNANCE.md](../GOVERNANCE.md) ·
[../docs/architecture/README.md](../docs/architecture/README.md) ·
[../docs/architecture/ADR/README.md](../docs/architecture/ADR/README.md) ·
[../docs/architecture/ADR/ADR-TEMPLATE.md](../docs/architecture/ADR/ADR-TEMPLATE.md)
