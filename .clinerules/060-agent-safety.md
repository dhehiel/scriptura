# 060 — Agent Safety

**Status:** Accepted · **Applies to:** agents, tooling, and all contributors · **Owner:** Maintainer

Scriptura implements **no autonomous agents at M0**. Agent behaviour is specified declaratively under
`agents/specs/`. Nothing observes, plans, or acts on its own initiative.

---

## 1. Standing prohibition

Until [BKB-AGENTS-001](../docs/architecture/BKB-AGENTS-001-agent-framework.md) is implemented at M5 or later,
under explicit maintainer authorisation:

1. **Do not implement autonomous agent execution.**
2. **Do not add scheduling, self-triggering, or cron-like recurrence** to project code.
3. **Do not add long-running loops** that select their own work.
4. **Do not add self-directed task selection.**
5. **Do not add an agent that writes to the corpus** without a human decision.
6. **Do not add an agent that promotes an epistemic layer.**
7. **Do not add an agent that mutates or deletes provenance.**
8. **Do not add an agent that determines a licence.**
9. **Do not add an agent that opens a milestone gate.**

An agent working *on* this repository is bound by these rules in the same way.

## 2. Capability boundaries

When agents are eventually implemented, each is granted an explicit, minimal capability set. Capabilities are
**deny-by-default**; an agent may do only what its specification permits.

| Capability | Default | Grant requires |
|---|---|---|
| Read corpus | Denied | Agent spec + maintainer approval |
| Read graph | Denied | Agent spec |
| Write `ai_hypothesis` records | Denied | Agent spec |
| Write any other layer | **Never** | Not grantable |
| Promote a layer | **Never** | Not grantable |
| Mutate provenance | **Never** | Not grantable |
| Ingest a dataset | **Never** | Not grantable |
| Determine a licence | **Never** | Not grantable |
| Execute code | **Never** | Not grantable |
| Network access | **Never** | Not grantable |
| Open a milestone gate | **Never** | Not grantable |

"Not grantable" means no specification, approval, or configuration may confer it. These boundaries are
architectural, not policy.

## 3. Mandatory human review

The following always require a human decision, recorded with identity and timestamp:

1. Any corpus ingestion.
2. Any licence determination.
3. Any epistemic layer promotion.
4. Any schema change.
5. Any architecture specification change.
6. Any deletion of provenance-bearing data.
7. Any milestone gate opening.
8. Any adoption of a new mandatory dependency.
9. Any change to these rules.

An agent may **draft, research, and recommend**. It may not **decide**.

## 4. Evidence obligations

An agent's output is admissible only if:

1. It carries the `ai_hypothesis` layer unless a source establishes otherwise.
2. Every factual assertion resolves to a citation.
3. It carries the model, method or prompt, inputs, and a confidence value.
4. It is flagged at every presentation boundary.
5. It does not contain generated scripture text.
6. It does not contain unattributed theological interpretation.
7. It records what it could not verify.

Output failing any condition is inadmissible and must not be persisted.

## 5. Output containment

1. **Agent output is quarantined by default.** It lands as `ai_hypothesis` and does not enter any
   authoritative layer.
2. **No agent output may be presented without its flag.** The flag is not removable by the consumer.
3. **No agent output may overwrite a sourced record.** Append-only.
4. **No agent output may be used as the sole basis for a downstream authoritative claim.**
5. **Agent runs are recorded** — inputs, outputs, model, timestamp, and outcome — under `agents/runs/`, which
   is a gitignored artefact zone.

## 6. Rate and scope limits

When agents are implemented:

1. **Bounded scope per run.** An agent operates on an explicitly enumerated scope, never "the whole corpus".
2. **Bounded output per run.** Volume limits prevent a flood of unreviewable output.
3. **Bounded cost.** Token, time, and storage budgets.
4. **Kill switch.** Every agent run is cancellable and every agent is disableable.
5. **Audit log.** Every action, append-only.

## 7. Failure behaviour

1. **Fail closed.** On any error, uncertainty, or ambiguity, an agent stops and reports. It does not guess.
2. **Never fabricate to complete a task.** An incomplete result is correct behaviour; a fabricated result is a
   defect. See [010-source-integrity.md](010-source-integrity.md).
3. **Escalate rather than degrade.** Where an obligation cannot be met, escalate.
4. **Do not retry into success.** Repeatedly re-running a failing operation hoping for a different answer is
   not verification.

## 8. Model and prompt provenance

1. Record the model identity and version.
2. Record the prompt or method, or a hash of it.
3. Record the inputs, by identifier.
4. Record the confidence.
5. Record the timestamp.

An `ai_hypothesis` record without generation provenance is rejected at validation.

## 9. Interaction with humans

1. **Never impersonate a human authority.** An agent does not write as "the project", "the maintainers", or a
   named scholar.
2. **Never present inference as consensus.**
3. **Disclose machine generation** in any human-facing output.
4. **Never argue a doctrinal position.** Agents report attributed positions; they do not advocate.

## 10. Verification before reporting **[human review]**

An agent may not report a task complete unless:

- [ ] The work was performed and the artefacts exist.
- [ ] Checks were actually run, and their output is reported.
- [ ] No obligation was silently dropped.
- [ ] Limitations and remaining work are stated.
- [ ] Nothing was claimed that was not done.

---

**Related:** [010-source-integrity.md](010-source-integrity.md) ·
[020-epistemic-layers.md](020-epistemic-layers.md) ·
[../AGENTS.md](../AGENTS.md) ·
[../docs/architecture/BKB-AGENTS-001-agent-framework.md](../docs/architecture/BKB-AGENTS-001-agent-framework.md) ·
[../docs/architecture/DKF-ARCH-001-discovery-framework.md](../docs/architecture/DKF-ARCH-001-discovery-framework.md)
