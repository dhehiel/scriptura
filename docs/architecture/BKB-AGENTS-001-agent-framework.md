# BKB-AGENTS-001 — Research Agent Framework

**Biblical Knowledge Base — Research Agent Framework**

| Field | Value |
|---|---|
| **ID** | BKB-AGENTS-001 |
| **Status** | Accepted |
| **Version** | 1.0.0 |
| **Milestone** | M0 (specification only — **no implementation**) |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Implementation** | **None. Declarative specifications only.** |
| **Supersedes** | — |

## Abstract

This specification defines the framework within which research agents may eventually operate in Scriptura: agent
contracts, capability boundaries, evidence obligations, output containment, audit requirements, and the human
review points that agents may never bypass. It is **specified at M0 and deliberately not implemented**. Nothing
in this repository observes, plans, or acts autonomously.

---

## 1. Purpose and scope

### 1.1 Purpose

Agents can produce a large volume of plausible-looking output far faster than a human can review it. In biblical
research, that asymmetry is the principal risk: an unreviewed fabrication becomes indexed, cross-referenced, and
eventually trusted.

This specification exists so that, when agents are eventually built, they are built **inside** a containment
structure rather than being contained after the fact.

### 1.2 In scope

Agent contracts; capability boundaries; evidence obligations; output containment; audit; human review points;
limits; failure behaviour.

### 1.3 Out of scope

Discovery semantics ([DKF-ARCH-001](DKF-ARCH-001-discovery-framework.md)); verification semantics
([BKB-VERIFY-001](BKB-VERIFY-001-verification-framework.md)); the layer model
([BKB-DATA-001](BKB-DATA-001-data-model.md)).

---

## 2. Implementation status at M0

> **No autonomous agents are implemented. This is a deliberate constraint, not an omission.**

| # | Fact |
|---|---|
| S1 | `agents/specs/` contains **declarative specifications only** |
| S2 | No agent executes |
| S3 | No scheduling, self-triggering, or recurrence exists in project code |
| S4 | No long-running loop selects its own work |
| S5 | No agent writes to the corpus |
| S6 | No agent promotes a layer |
| S7 | No agent mutates provenance |
| S8 | `agents/runs/` is an empty, gitignored artefact zone |

Implementation is not scheduled before **M5**, and requires explicit maintainer authorisation. See
[../milestones/ROADMAP.md](../milestones/ROADMAP.md).

An agent working *on* this repository is bound by the same constraints. See
[../../AGENTS.md](../../AGENTS.md) and [.clinerules/060-agent-safety.md](../../.clinerules/060-agent-safety.md).

---

## 3. Design principles

| # | Principle | Consequence |
|---|---|---|
| AG1 | **Deny by default** | An agent may do only what its specification explicitly permits |
| AG2 | **Containment before capability** | Output is quarantined as `ai_hypothesis` until evidence and review establish otherwise |
| AG3 | **Agents recommend; humans decide** | No agent holds decision authority over anything normative |
| AG4 | **Fail closed** | On error, uncertainty, or ambiguity, an agent stops and reports |
| AG5 | **Never fabricate to complete** | An incomplete result is correct behaviour; a fabricated one is a defect |
| AG6 | **Bounded scope** | An agent operates on an enumerated scope, never "the whole corpus" |
| AG7 | **Everything is audited** | Every action is recorded, append-only |
| AG8 | **Reversibility** | Agent effects are reversible; nothing an agent does is irreversible |
| AG9 | **Layer honesty** | An agent classifies its own output correctly, defaulting to the weakest layer |

---

## 4. Agent contract

An agent specification is a declarative document, schema-validated against
[`schemas/agents/agent-spec.schema.json`](../../schemas/agents/agent-spec.schema.json).

### 4.1 Required fields

| Field | Requirement |
|---|---|
| `agent_id` | Stable identifier |
| `name`, `description` | Human-readable |
| `purpose` | The research question the agent serves |
| `status` | `proposed`, `approved`, `disabled`. Nothing runs unless `approved` |
| `capabilities` | Explicit list. Deny-by-default |
| `scope` | Enumerated. What the agent may operate on |
| `input_layers` | Which layers it may read |
| `output_layer` | Which layer it may write. **Only `ai_hypothesis` is grantable** |
| `evidence_obligations` | What it must produce for its output to be admissible |
| `limits` | Volume, cost, time, iteration bounds |
| `human_review_points` | Where a human must intervene |
| `failure_behaviour` | What it does on error |
| `audit` | What it records |
| `owner`, `approved_by`, `approved_at` | Accountability |
| `disable_conditions` | When it must be disabled |

### 4.2 Contract invariants

| # | Invariant |
|---|---|
| AC1 | An agent with `status != approved` cannot run |
| AC2 | An agent's `output_layer` is `ai_hypothesis`. No other value is grantable |
| AC3 | An agent's `scope` is enumerated and bounded |
| AC4 | An agent's capabilities are a subset of the grantable set (§5) |
| AC5 | An agent specification is immutable once approved. Change requires a new version |
| AC6 | An agent without `human_review_points` cannot be approved |
| AC7 | An agent without `limits` cannot be approved |

---

## 5. Capability boundaries

Capabilities are **deny-by-default**. Some are **not grantable** — no specification, approval, or configuration
may confer them. These boundaries are architectural, not policy.

| Capability | Default | Grantable? | Grant requires |
|---|---|---|---|
| Read corpus | Denied | Yes | Agent spec |
| Read graph | Denied | Yes | Agent spec |
| Read licences and registries | Denied | Yes | Agent spec |
| Write `ai_hypothesis` records | Denied | Yes | Agent spec + maintainer approval |
| Query FTS5 | Denied | Yes | Agent spec |
| Query optional semantic backend | Denied | Yes | Agent spec + backend present |
| Write to any layer other than `ai_hypothesis` | Denied | **Never** | — |
| Promote or demote a layer | Denied | **Never** | — |
| Mutate or delete provenance | Denied | **Never** | — |
| Ingest a dataset | Denied | **Never** | — |
| Retrieve from the network | Denied | **Never** | — |
| Determine or alter a licence | Denied | **Never** | — |
| Execute code | Denied | **Never** | — |
| Open a milestone gate | Denied | **Never** | — |
| Modify an agent specification | Denied | **Never** | — |
| Approve another agent | Denied | **Never** | — |
| Alter the schema or migrations | Denied | **Never** | — |

### 5.1 Why some capabilities are never grantable

Each "never" removes a class of catastrophic failure rather than mitigating it:

- **Writing to non-`ai_hypothesis` layers** would let inference acquire the warrant of evidence by storage.
- **Layer promotion** would let an agent launder its own output.
- **Provenance mutation** would destroy the audit trail that makes detection possible.
- **Ingestion and retrieval** would let an agent take on legal responsibility for data.
- **Licence determination** is a legal judgement requiring primary-source evidence and human accountability.
- **Code execution** would make containment unenforceable.
- **Gate opening and self-approval** would let an agent authorise itself.

---

## 6. Evidence obligations

An agent's output is **admissible** only if all hold. Inadmissible output must not be persisted.

| # | Obligation |
|---|---|
| E1 | Carries the `ai_hypothesis` layer, unless a cited source establishes a stronger warrant |
| E2 | Every factual assertion resolves to a citation |
| E3 | Carries `model` — identity and version |
| E4 | Carries `method` — prompt or method, or a hash of it |
| E5 | Carries `inputs` — input identifiers |
| E6 | Carries `confidence` in `[0, 1]` |
| E7 | Carries `generated_at` |
| E8 | Is flagged `non_authoritative` |
| E9 | Contains **no generated scripture text** |
| E10 | Contains **no unattributed theological interpretation** |
| E11 | Records what it could **not** verify |
| E12 | Records null results as null |
| E13 | Preserves disagreement rather than resolving it |
| E14 | Contains no invented identifiers, sigla, DOIs, or catalogue numbers |

E11–E14 are as binding as E1–E10. An agent that reports only what it found, and not what it failed to find, has
not discharged its obligation.

---

## 7. Output containment

| # | Rule |
|---|---|
| OC1 | Agent output is quarantined as `ai_hypothesis` on arrival |
| OC2 | Output does not enter any authoritative layer |
| OC3 | Output is never presented without its flag; the flag is not removable by the consumer |
| OC4 | Output never overwrites a sourced record. Append-only |
| OC5 | Output is never the **sole** basis for a downstream authoritative claim |
| OC6 | Output mixing layers must visibly distinguish them |
| OC7 | Exports of agent output carry layer and flag information |
| OC8 | An agent run record is written for every run, whether it produced output or not |

---

## 8. Audit

Every run produces a run record, schema-validated against
[`schemas/agents/agent-run.schema.json`](../../schemas/agents/agent-run.schema.json).

| Field | Requirement |
|---|---|
| `run_id` | Mandatory |
| `agent_id`, `agent_spec_version` | Mandatory |
| `started_at`, `finished_at` | Mandatory |
| `status` | `completed`, `failed`, `cancelled`, `halted` |
| `scope` | What it actually operated on |
| `inputs` | Input identifiers |
| `outputs` | Output identifiers |
| `model`, `method_hash` | Mandatory |
| `records_created`, `records_rejected` | Mandatory |
| `limits_consumed` | Tokens, time, iterations |
| `human_review` | Who reviewed, when, and the decision |
| `failure_reason` | Where status is not `completed` |
| `verification_results` | Links to verification records |

Run records are **append-only** and stored in `agents/runs/`, which is a gitignored artefact zone. Summaries may
be committed; raw run artefacts are not.

---

## 9. Human review points

The following **always** require a human decision, recorded with identity and timestamp. An agent may draft,
research, and recommend. It may not decide.

| # | Decision |
|---|---|
| H1 | Any corpus ingestion |
| H2 | Any licence determination |
| H3 | Any epistemic layer promotion |
| H4 | Any schema change |
| H5 | Any architecture specification change |
| H6 | Any deletion of provenance-bearing data |
| H7 | Any milestone gate opening |
| H8 | Any adoption of a new mandatory dependency |
| H9 | Any change to `.clinerules/` |
| H10 | Approval, disabling, or version change of any agent specification |
| H11 | Acceptance of any agent output into a review queue as a candidate finding |

An agent specification that names no human review point **cannot be approved** (AC6).

---

## 10. Limits

| Limit | Purpose |
|---|---|
| **Scope bound** | An agent operates on an enumerated scope. "The whole corpus" is not a scope |
| **Volume bound** | Prevents a flood of unreviewable output |
| **Cost bound** | Token, compute, and time budgets |
| **Iteration bound** | Prevents unbounded loops |
| **Storage bound** | Prevents unbounded artefact growth |
| **Kill switch** | Every run is cancellable; every agent is disableable |

An agent exceeding any bound **halts** and reports. It does not request an increase; a human grants one.

---

## 11. Failure behaviour

| # | Rule |
|---|---|
| F1 | **Fail closed.** On error, uncertainty, or ambiguity, stop and report |
| F2 | **Never fabricate to complete a task** |
| F3 | **Escalate rather than degrade.** Where an obligation cannot be met, escalate |
| F4 | **Do not retry into success.** Re-running a failing operation hoping for a different answer is not verification |
| F5 | **Report partial results as partial** |
| F6 | **Record the failure** in the run record with a reason |
| F7 | **Preserve work already done.** A failure does not discard valid partial output |
| F8 | **A halted agent does not resume itself** |

---

## 12. Interaction norms

| # | Rule |
|---|---|
| IN1 | Never impersonate a human authority. An agent does not write as "the project", "the maintainers", or a named scholar |
| IN2 | Never present inference as consensus |
| IN3 | Disclose machine generation in any human-facing output |
| IN4 | Never argue a doctrinal position. Agents report attributed positions; they do not advocate |
| IN5 | Never resolve a canonical or doctrinal disagreement |
| IN6 | Attribute living scholars and respect their rights |

---

## 13. Prohibitions

| # | Prohibition |
|---|---|
| P1 | Implementing autonomous execution before M5 and without authorisation |
| P2 | Scheduling, self-triggering, or recurrence |
| P3 | Self-directed task selection |
| P4 | Writing to any layer other than `ai_hypothesis` |
| P5 | Promoting or demoting a layer |
| P6 | Mutating or deleting provenance |
| P7 | Ingesting or retrieving |
| P8 | Determining a licence |
| P9 | Executing code |
| P10 | Self-approval or self-modification of a specification |
| P11 | Emitting unflagged output |
| P12 | Generating scripture text |
| P13 | Emitting unattributed theological interpretation |
| P14 | Inventing identifiers or citations |
| P15 | Reporting completion of unperformed work |

---

## 14. Verification

At M0, verification confirms **absence** rather than behaviour:

| Check | Command |
|---|---|
| No agent execution code exists | `python -m unittest tests.test_agents_absent` |
| Agent specs directory contains no runnable code | `make check` |
| Agent spec schema is valid | `python -m unittest tests.test_schemas` |
| Agent run schema is valid | `python -m unittest tests.test_schemas` |
| No scheduling or recurrence in project code | `python -m unittest tests.test_dependency_hygiene` |
| Full suite | `make test` |

When agents are implemented, this section is revised to add behavioural verification, and the revision requires
an ADR.

---

## 15. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.0.0 | M0 | Initial specification. **Specified, not implemented.** Capability boundaries, evidence obligations, output containment, audit, human review points, limits, failure behaviour. | — |
