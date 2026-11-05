# Milestones

Scriptura's milestone planning.

> **Milestones are gated, not scheduled.** A milestone opens only when its predecessor's exit criteria are met
> **and** the maintainer records that they are met. Readiness is not authorisation.

| Document | Purpose |
|---|---|
| [ROADMAP.md](ROADMAP.md) | The M0–M5 plan, with scope and gating conditions per milestone |
| [M0-acceptance-criteria.md](M0-acceptance-criteria.md) | M0 exit criteria, with per-criterion evidence and verification commands |

---

## Current position

| Item | Value |
|---|---|
| Current milestone | **M0 — Architecture Foundation** |
| Criteria A–H | Met, with evidence |
| Criterion I1 — human architecture review | **Not met** |
| M0 → M1 gate | **CLOSED** |
| Corpus data present | **None** |
| Corpus ingestion | **Prohibited** |
| Next action | Human architecture review of the six specifications |

---

## Gating rules

1. A gate is satisfied by **evidence**, not assertion. Each criterion names the command or artefact that
   demonstrates it.
2. The M0 → M1 gate additionally requires a **completed architecture review by a human reviewer**, recorded
   with identity and date. This cannot be satisfied by CI, by an agent, or by self-attestation.
3. Until a gate opens, work belonging to the next milestone is out of scope **regardless of how ready the code
   appears**.
4. Opening a gate is recorded in the milestone document with date, approver identity, per-criterion evidence,
   and any waived criteria with reasons. A gate opened without a record is not open.

See [../../GOVERNANCE.md](../../GOVERNANCE.md) and
[../../.clinerules/000-project-governance.md](../../.clinerules/000-project-governance.md) §5.

---

## Verifying

```bash
make check && make test
```
