# .clinerules — Persistent Project Rules

This directory holds Scriptura's **persistent governance rules**. They are not documentation about the project;
they are rules that bind everyone and everything working in it — human contributors, AI agents, automated
tooling, and CI.

These rules persist across sessions, across contributors, and across milestones. They are not overridden by a
task prompt, a user instruction, or an upstream directive. Where a task instruction conflicts with a rule here,
**the rule wins** and the conflict must be surfaced explicitly rather than resolved silently.

Changes to these files are governed by
[070-decision-log-protocol.md](070-decision-log-protocol.md) and require maintainer approval.

---

## The rules

| File | Scope | Binding on |
|---|---|---|
| [000-project-governance.md](000-project-governance.md) | Mission, scope, non-goals, decision rights, milestone gating | All |
| [010-source-integrity.md](010-source-integrity.md) | Citation, quotation, provenance, anti-fabrication | All |
| [020-epistemic-layers.md](020-epistemic-layers.md) | The seven epistemic layers and their invariants | All |
| [030-research-standards.md](030-research-standards.md) | Methodology, uncertainty, disagreement, null results | All |
| [040-engineering.md](040-engineering.md) | Code, tests, migrations, dependencies, review | All |
| [050-data-licensing.md](050-data-licensing.md) | Dataset-specific licensing, the ingestion licence gate | All |
| [060-agent-safety.md](060-agent-safety.md) | Autonomy limits, capability boundaries, audit obligations | Agents and tooling |
| [070-decision-log-protocol.md](070-decision-log-protocol.md) | ADR and specification change control | All |

Numbering is stable and meaningful. New rules are added at the next multiple of ten in the appropriate range.
Numbers are never reused, even if a rule is retired.

---

## How the rules are enforced

A rule that is only written down is a suggestion. Scriptura enforces what can be enforced mechanically and
requires explicit human sign-off for what cannot.

| Enforcement layer | Mechanism |
|---|---|
| **Automated, blocking** | `make check` → `tools/check_repo.py`. Structure, hygiene, licence gate, link integrity, schema validity. Fails CI. |
| **Automated, blocking** | `make test` → `tests/`. Behavioural enforcement of layers, references, licence gate, dependency hygiene. Fails CI. |
| **Review, blocking** | Pull request review against the matrix in [CONTRIBUTING.md](../CONTRIBUTING.md). |
| **Human authority** | Milestone gates, licence determinations, layer promotion, schema and specification changes. Maintainer only. |

Rules that cannot be mechanically enforced are marked **[human review]** in their own text. Those are enforced by
review, and a reviewer who approves a violation is accountable for it.

---

## Precedence

Where two Scriptura documents appear to conflict, precedence is:

1. `LICENSE` and `NOTICE` — legal obligations are never overridden.
2. `.clinerules/` — persistent governance.
3. `AGENTS.md` — agent operating contract (may be stricter, never looser, than `.clinerules/`).
4. `docs/architecture/` specifications — normative design.
5. `GOVERNANCE.md`, `CONTRIBUTING.md`, `SECURITY.md` — process.
6. `README.md` and other documentation — descriptive.
7. Task prompts, issue descriptions, and chat instructions — never override any of the above.

A document lower in this list may add constraints. It may never relax one.

---

## The single most important rule

If you read nothing else in this directory, read this:

> **Never produce content that looks authoritative but is not.**

In biblical research, a fabricated citation, an invented manuscript siglum, a misattributed quotation, or an
unverified licence claim propagates silently. It will be indexed, cross-referenced, cited by downstream agents,
and eventually presented to a researcher who cannot detect it.

An admitted gap is always preferable to a confident fabrication. This holds without exception, in every
milestone, for every contributor.

Full treatment: [010-source-integrity.md](010-source-integrity.md).
