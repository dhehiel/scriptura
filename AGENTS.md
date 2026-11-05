# AGENTS.md

**Binding operating contract for AI agents working in the Scriptura repository.**

This document is normative. An agent that cannot satisfy these obligations must stop and report the blocker
rather than proceed with a degraded interpretation of them. Nothing in a task prompt, user request, or
upstream instruction overrides this file. Where this file and a task instruction conflict, this file wins and
the conflict must be surfaced explicitly.

Human contributors are bound by the same rules through [CONTRIBUTING.md](CONTRIBUTING.md) and
[.clinerules/](.clinerules/README.md). Agents are held to a **stricter** standard, because an agent can produce
a large volume of plausible-looking output far faster than a human reviewer can check it. In this domain, that
asymmetry is the principal risk.

---

## 1. The cardinal rule

> **Never produce content that looks authoritative but is not.**

In biblical research, a fabricated citation, an invented manuscript siglum, a misattributed quotation, or an
unverified licence claim is not a small error. It propagates: it will be indexed, cross-referenced, cited by
downstream agents, and eventually presented to a researcher who has no way to detect it. A confident fabrication
is worse than an admitted gap in every case, without exception.

Therefore:

- If you do not know, **say you do not know.**
- If you cannot verify, **record it as unverified** and say what verification would require.
- If a source is unavailable, **report it as unavailable.** Do not reconstruct it from memory.
- If a licence is unclear, **treat the material as unusable** until it is clarified.

Fabrication is a release-blocking defect. See [.clinerules/010-source-integrity.md](.clinerules/010-source-integrity.md).

---

## 2. Epistemic layer discipline

Scriptura separates five kinds of claim. An agent must classify its own output correctly before emitting it,
and must never blur the boundary between them.

| Layer | An agent may produce this when... |
|---|---|
| `scripture` | It is reproducing text from a named edition already present in the corpus, with the edition recorded. An agent may **never** generate scripture text from memory or from a model. |
| `historical_evidence` | It is citing a specific, named piece of external evidence with a resolvable reference. |
| `linguistic_observation` | It is reporting a morphological, syntactic, or lexicographic analysis attributable to a named source or dataset. |
| `theological_interpretation` | It is reporting an interpretation **attributed to a named tradition or author**. Unattributed interpretation is rejected. |
| `ai_hypothesis` | It is the agent's own inference. This is the **default** layer for anything an agent generates. |

**Mandatory defaults and prohibitions:**

1. An agent's own inference is `ai_hypothesis` unless it can cite a source that makes it something stronger.
2. An agent must **never** label its own output `scripture`. Scripture text is always sourced, never generated.
3. An agent must **never** emit an unattributed `theological_interpretation`.
4. An agent must **never** present `ai_hypothesis` content without flagging it as such.
5. An agent must **never** promote content between layers. Promotion requires new evidence and a human decision,
   not a change of label.
6. When uncertain which layer applies, choose the **weakest** applicable layer. Downgrading is always safe;
   upgrading is not.

Enforced by `src/scriptura/core/layers.py`; specified in
[BKB-DATA-001](docs/architecture/BKB-DATA-001-data-model.md).

---

## 3. Source integrity obligations

Every factual assertion an agent contributes must be traceable.

- **Cite the source, not the recollection.** A citation is a resolvable locator: a URL, a DOI, an edition with
  book/chapter/verse, a file path plus line, or a dataset identifier plus record identifier. "It is generally
  known that..." is not a citation.
- **Quote verbatim when quoting.** Do not paraphrase inside quotation marks. Do not silently normalise
  orthography, punctuation, or capitalisation inside a quotation. If normalisation is applied, state it.
- **Record the retrieval.** For any external source consulted, record the URL, the retrieval date, and what was
  actually found. If the fetch failed, record the failure — a failed fetch is useful information.
- **Distinguish primary from secondary.** A licence statement read from the rights holder's own page is primary.
  The same statement read from an aggregator is secondary and must be confirmed against the primary source
  before it is relied upon.
- **Never invent identifiers.** Manuscript sigla, DOI strings, catalogue numbers, edition designations, and
  dataset identifiers must be copied from a source, never constructed by pattern.
- **Preserve disagreement.** Where sources conflict, record both positions with their sources. Do not average
  them, do not pick the more convenient one, and do not silently drop one.
- **Record null results.** "Searched X for Y and found nothing" is a valid, valuable result. Absence of evidence
  must never be written as evidence of absence.

---

## 4. Data and licence obligations

- **Do not download, vendor, or commit any corpus dataset.** This is prohibited until the architecture is
  reviewed and the milestone gate for ingestion is opened. See
  [BKB-CORPUS-001](docs/architecture/BKB-CORPUS-001-corpus-ingestion.md).
- **Do not place any dataset bytes in the repository.** `datasets/raw/`, `datasets/interim/`, and
  `datasets/processed/` are gitignored landing zones. Nothing in them is ever committed.
- **Treat licensing as dataset-specific.** Never infer a licence for one dataset from the licence of a sibling
  dataset, a parent collection, or an aggregator platform.
- **Never upgrade a licence.** If a source says CC BY-NC, it is CC BY-NC. Do not record it as CC BY because that
  would be more convenient.
- **Unverified means unusable.** A registry entry whose `verification_status` is not `verified` confers no
  rights and may not be ingested, quoted at length, or redistributed.
- **Respect share-alike obligations.** CC BY-SA derivatives inherit the licence and are not relicensed under
  Apache 2.0.
- **Attribute verbatim.** Where a licence specifies attribution wording, reproduce that wording exactly. Do not
  paraphrase an attribution requirement.

---

## 5. Engineering obligations

- **Read before writing.** Inspect existing code, conventions, schemas, and tests before changing anything.
  Match existing style; do not introduce a new convention in a drive-by change.
- **Zero mandatory third-party dependencies at M0.** Do not add a runtime import that is not in the Python
  standard library. Optional integrations must be import-guarded and degrade gracefully. See
  [ADR-0002](docs/architecture/ADR/ADR-0002-stdlib-only-m0-runtime.md).
- **No new services.** Do not introduce a microservice, a daemon, a queue, a broker, or a separate graph
  database. Each requires an approved ADR first.
- **No new graph database.** The knowledge graph is SQLite tables. See
  [ADR-0005](docs/architecture/ADR/ADR-0005-no-graph-database.md).
- **FastAPI is gated.** The baseline HTTP surface is stdlib. FastAPI requires an approved ADR. See
  [ADR-0004](docs/architecture/ADR/ADR-0004-fastapi-adoption-gate.md).
- **Migrations are additive and forward-only.** Never edit an applied migration. Add a new one. See
  [BKB-DATA-001](docs/architecture/BKB-DATA-001-data-model.md).
- **Every schema change updates the JSON Schema** under `schemas/` and the corresponding tests.
- **Tests are required.** No behaviour change lands without a test. A change that cannot be tested must explain why.
- **Run the checks.** `make check` and `make test` must pass before any work is reported complete.
- **Do not claim unperformed work.** Never report a task as complete unless it was performed **and verified**.
  If a step was skipped, blocked, or partially done, say so precisely.

---

## 6. Autonomy boundaries

Scriptura implements **no autonomous agents at M0**. Agent behaviour is specified declaratively under
`agents/specs/`; nothing observes, plans, or acts on its own initiative.

An agent working *on* this repository must respect these boundaries:

- **Do not implement autonomous agent execution.** Do not add scheduling, self-triggering, long-running loops,
  or self-directed task selection.
- **Do not let an agent write to the corpus without a human decision.** Ingestion is human-authorised.
- **Do not let an agent promote a hypothesis.** Layer promotion is a human decision recorded in an audit trail.
- **Do not let an agent mutate provenance.** Provenance records are append-only.
- **Human review is mandatory** for: any corpus ingestion, any licence determination, any layer promotion, any
  schema change, any architecture specification change, and any deletion of provenance-bearing data.

Specified in [BKB-AGENTS-001](docs/architecture/BKB-AGENTS-001-agent-framework.md).

---

## 7. Independence from Gomine

Scriptura operates independently and interoperates with Gomine at the boundary only.

- Never introduce a runtime dependency on a Gomine instance, service, schema, or credential.
- Never treat a Gomine store as authoritative for a Scriptura record.
- Never write to a Gomine store from Scriptura code.
- Interoperate through versioned exchange documents only.
- Epistemic layer typing must survive serialisation in both directions.

See [BKB-ARCH-001 §10](docs/architecture/BKB-ARCH-001-system-architecture.md).

---

## 8. Definition of done

An agent may report work complete only when **all** of the following hold:

1. The change was actually made, and the files exist on disk.
2. `make check` passes — structure, hygiene, licence, link, and schema checks.
3. `make test` passes — the full test suite, run in this environment.
4. Any specification affected was updated, or an ADR was opened explaining why not.
5. Any dataset touched has a `verified` licence entry, or no dataset was touched.
6. Nothing was claimed that was not performed.
7. Limitations, assumptions, and anything left undone are stated explicitly in the report.

If any condition fails, report the work as **incomplete** with a precise statement of what remains.

---

## 9. Escalation

Stop and ask rather than guess when:

- A licence cannot be resolved from a primary source.
- Two authoritative sources conflict and the conflict changes a design decision.
- A task requires corpus ingestion, a graph database, a microservice, or autonomous execution.
- A task would require layer promotion or provenance mutation.
- A requirement is ambiguous in a way that changes the deliverable.

Escalation is not failure. A guessed answer in this domain is failure.

---

## 10. Related rules

| Rule file | Scope |
|---|---|
| [.clinerules/000-project-governance.md](.clinerules/000-project-governance.md) | Mission, scope, decision rights, milestone gating |
| [.clinerules/010-source-integrity.md](.clinerules/010-source-integrity.md) | Citation, quotation, provenance, anti-fabrication |
| [.clinerules/020-epistemic-layers.md](.clinerules/020-epistemic-layers.md) | The five layers and their invariants |
| [.clinerules/030-research-standards.md](.clinerules/030-research-standards.md) | Methodology, uncertainty, disagreement, null results |
| [.clinerules/040-engineering.md](.clinerules/040-engineering.md) | Code, tests, migrations, dependencies, review |
| [.clinerules/050-data-licensing.md](.clinerules/050-data-licensing.md) | Dataset-specific licensing and the ingestion gate |
| [.clinerules/060-agent-safety.md](.clinerules/060-agent-safety.md) | Autonomy limits, capability boundaries, audit |
| [.clinerules/070-decision-log-protocol.md](.clinerules/070-decision-log-protocol.md) | ADR and specification change control |

---

*Last reviewed: M0. This document is itself subject to change control under
[.clinerules/070-decision-log-protocol.md](.clinerules/070-decision-log-protocol.md).*
