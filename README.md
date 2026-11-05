# Scriptura

**An open, extensible Biblical Knowledge and Research Infrastructure for scripture, original-language analysis, historical context, theological research, and cross-disciplinary knowledge discovery.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)](#requirements)
[![Milestone](https://img.shields.io/badge/milestone-M0%20--%20architecture%20foundation-orange.svg)](docs/milestones/README.md)
[![Corpus data](https://img.shields.io/badge/corpus%20data-none%20ingested-lightgrey.svg)](docs/data/README.md)

---

## Current status: M0 — architecture foundation only

> [!IMPORTANT]
> This repository currently contains **architecture, governance, schemas, and infrastructure scaffolding only**.
>
> As of M0:
> - **No Bible text, translation, lexicon, or corpus dataset has been downloaded, vendored, or committed.**
> - **No autonomous agents are implemented.** Agent contracts and safety rules are specified declaratively; nothing executes autonomously.
> - **No graph database is present.** The knowledge graph is a modular relational model over SQLite.
> - **No microservices exist.** Scriptura is a single-process, single-file-database application.
> - **The runtime has zero mandatory third-party Python dependencies.**
>
> Corpus ingestion is deliberately gated behind architecture review. See
> [M0 acceptance criteria](docs/milestones/M0-acceptance-criteria.md) and
> [BKB-CORPUS-001](docs/architecture/BKB-CORPUS-001-corpus-ingestion.md).
>
> These statements are machine-checked. Run `make check` to verify them yourself.

---

## What Scriptura is

Scriptura is infrastructure, not a product. It exists so that biblical research questions can be asked against
**provenanced** data with **auditably separated** kinds of claim.

The central problem in biblical computing is not the absence of data. It is that data of radically different
epistemic kinds is routinely flattened into a single undifferentiated store, so that a manuscript reading, an
archaeological date, a morphological parse, a patristic interpretation, and a machine-generated guess become
indistinguishable once queried together.

Scriptura's foundational commitment is that these are **never** interchangeable, and the data model makes it
structurally impossible to treat them as if they were.

### The five epistemic layers

Every record in Scriptura carries exactly one epistemic layer. Layers are enforced at the type level, at the
storage level, and at the query level. See [BKB-DATA-001](docs/architecture/BKB-DATA-001-data-model.md).

| Layer | What it is | Example | Authority |
|---|---|---|---|
| `scripture` | Text of a witness as attested by a **named edition** | "Codex Vaticanus reads *X* at John 1:18" | The edition is the authority, never "the Bible" |
| `historical_evidence` | Material and documentary evidence **external** to scripture | An inscription, an ostracon, a dated papyrus, a historian's account | Evidence stands on its own; it does not inherit scriptural authority |
| `linguistic_observation` | Morphology, syntax, lexicography, philology | "*monogenēs* parses as adjective, singular, nominative" | Analytical; contested readings carry competing analyses |
| `theological_interpretation` | Interpretive positions of **named** traditions and authors | "Augustine reads this passage as Trinitarian" | Attributed to a tradition or author; never presented as fact |
| `ai_hypothesis` | Machine-generated inference | A model's proposed intertextual link | **Always non-authoritative.** Must be flagged in every output |

Three rules follow, and they are enforced by code rather than by convention:

1. **No layer may be promoted to another.** An AI hypothesis cannot become a linguistic observation by being stored.
2. **`ai_hypothesis` output must be flagged at every presentation boundary**, including API responses, exports, and reports.
3. **`theological_interpretation` must carry an attribution.** An interpretation with no named tradition or author is rejected at validation.

---

## Repository layout

```
scriptura/
├── .clinerules/              Persistent governance rules (binding on all agents and humans)
├── .github/                  CI workflows, issue and PR templates
├── docs/
│   ├── architecture/         The six foundational specifications + ADRs
│   ├── data/                 Dataset source registry and licence manifest
│   ├── milestones/           M0 acceptance criteria and the milestone plan
│   ├── research/             Research methodology and standards
│   └── operations/           Runbooks and operational guidance
├── datasets/                 Corpus landing zone (EMPTY at M0 — never commit data here)
│   ├── raw/                  Immutable bytes as retrieved from upstream
│   ├── interim/              Parsed but not yet validated
│   ├── processed/            Validated, schema-conformant, licence-cleared
│   ├── manifests/            Per-dataset provenance manifests
│   └── third_party/          Vendored upstream material, if ever permitted
├── schemas/                  JSON Schema definitions (core, data, agents, verification)
├── src/scriptura/            Source code
│   ├── core/                 References, epistemic layers, hashing, errors
│   ├── storage/              SQLite connection management and migrations
│   ├── graph/                Modular knowledge graph over SQLite
│   ├── search/               SQLite FTS5 lexical search
│   ├── retrieval/            Optional LEANN semantic retrieval adapter
│   ├── ingestion/            Licence-gated ingestion pipeline framework
│   ├── provenance/           Licence manifest and source registry enforcement
│   ├── schemas/              Stdlib JSON Schema subset validator
│   └── api/                  Read-only HTTP surface (stdlib), FastAPI optional
├── agents/                   Agent specifications (declarative only at M0 — nothing runs)
├── evaluation/               Benchmarks, evaluation datasets, reports
├── tests/                    Test suite (stdlib unittest; pytest-compatible)
└── tools/                    Repository and documentation checkers
```

See [docs/README.md](docs/README.md) for the full documentation index.

---

## Technology architecture

Chosen for durability, auditability, and the ability to run on a laptop. Rationale for each choice is recorded
in an Architecture Decision Record; none of these is incidental.

| Concern | Decision | Rationale |
|---|---|---|
| Language | **Python 3.11+** | Ecosystem depth for philological and ML work; stdlib-only runtime at M0 |
| Primary store | **SQLite** | Single file, zero server, durable, transactional, universally auditable. [ADR-0001](docs/architecture/ADR/ADR-0001-sqlite-as-primary-store.md) |
| Lexical search | **SQLite FTS5 + explicit Unicode folding** | In-database full-text index. FTS5's built-in folding covers Latin only; Greek and Hebrew are folded explicitly into a separate indexed column — union matching, no transliteration, stored text untouched. [ADR-0009](docs/architecture/ADR/ADR-0009-fts5-primary-lexical-search.md) |
| Knowledge graph | **Modular graph over SQLite** | Typed nodes and edges as relational tables. No separate graph database. [ADR-0005](docs/architecture/ADR/ADR-0005-no-graph-database.md), [ADR-0007](docs/architecture/ADR/ADR-0007-modular-knowledge-graph.md) |
| Semantic retrieval | **Optional LEANN adapter** | Pluggable, import-guarded, MIT-licensed. Absent by default; FTS5 remains the baseline. [ADR-0006](docs/architecture/ADR/ADR-0006-leann-optional-retrieval.md) |
| HTTP surface | **stdlib `http.server`; FastAPI gated** | FastAPI adopted only behind an approved ADR showing justification. [ADR-0004](docs/architecture/ADR/ADR-0004-fastapi-adoption-gate.md) |
| Dependencies | **Zero mandatory third-party deps at M0** | Minimises supply-chain and licence risk. [ADR-0002](docs/architecture/ADR/ADR-0002-stdlib-only-m0-runtime.md) |

### Explicit non-goals at M0

These are constraints, not omissions. Each is enforced by `.clinerules/` and checked in CI.

- **No corpus ingestion.** No dataset is fetched until the architecture is reviewed and the licence manifest entry exists.
- **No autonomous agents.** Agents are specified, not implemented. Nothing observes, plans, or acts on its own.
- **No microservices.** One process, one database file. Splitting a service out requires an ADR.
- **No graph database.** Introducing Neo4j, or any equivalent, requires an approved ADR that first demonstrates why SQLite cannot satisfy the requirement.
- **No licence assumptions.** Every dataset is licensed individually. Aggregator-level licences are never treated as sufficient.

---

## Requirements

**Runtime:** Python 3.11 or newer, and a SQLite build with FTS5 and JSON1 enabled. Nothing else.

Verify your platform satisfies this:

```bash
python3 -c "from scriptura.storage.sqlite import capability_report; print(capability_report())"
```

**Optional:**

- `leann` — enables the semantic retrieval adapter. Without it, Scriptura uses FTS5 only.
- `fastapi` — enables the FastAPI HTTP surface, if adopted by ADR.
- Development extras (`pytest`, `ruff`, `mypy`) — see `pyproject.toml`.

---

## Quick start

The package runs from source with no network access required:

```bash
git clone https://github.com/dhehiel/scriptura.git
cd scriptura
export PYTHONPATH=src
```

Create and inspect an empty knowledge base:

```bash
python3 tools/build_db.py --db /tmp/scriptura.db
python3 -m scriptura.api.server --db /tmp/scriptura.db --describe
```

Verify the repository against its own governance rules:

```bash
make check          # structure, hygiene, licences, links, schemas
make test           # full test suite
```

---

## Architecture specifications

The six foundational specifications. All are normative. Where a specification and an implementation disagree,
the specification wins and the implementation is a bug.

| ID | Title | Governs |
|---|---|---|
| [BKB-ARCH-001](docs/architecture/BKB-ARCH-001-system-architecture.md) | System Architecture | Overall system decomposition, process model, module boundaries, Gomine interoperability |
| [BKB-DATA-001](docs/architecture/BKB-DATA-001-data-model.md) | Data Model and Epistemic Layers | The five layers, provenance, references, relational schema, invariants |
| [BKB-CORPUS-001](docs/architecture/BKB-CORPUS-001-corpus-ingestion.md) | Corpus Ingestion | Dataset lifecycle, licence gate, adapters, validation, provenance capture |
| [BKB-AGENTS-001](docs/architecture/BKB-AGENTS-001-agent-framework.md) | Research Agent Framework | Agent contracts, capability boundaries, evidence obligations, human review |
| [BKB-VERIFY-001](docs/architecture/BKB-VERIFY-001-verification-framework.md) | Verification Framework | Claim verification, evidence chains, confidence, disagreement handling |
| [DKF-ARCH-001](docs/architecture/DKF-ARCH-001-discovery-framework.md) | Discovery and Knowledge Framework | Hypothesis generation, cross-domain linking, hypothesis→candidate→verified lifecycle |

Architecture decisions that constrain or extend these specifications are recorded in
[docs/architecture/ADR/](docs/architecture/ADR/README.md). Numbering, status, and change rules are in
[docs/architecture/README.md](docs/architecture/README.md).

---

## Milestones

| Milestone | Scope | Status |
|---|---|---|
| **M0** | Architecture foundation: documentation, governance, schemas, storage core, verification harness. **No corpus data.** | **In review** |
| **M1** | Reference core and single-edition text ingestion, with full provenance. Gated on M0 architecture review. | Not started |
| **M2** | Multi-witness alignment, variants, and original-language morphology. | Not started |
| **M3** | Knowledge graph population and cross-reference discovery. | Not started |
| **M4** | Verification framework in production and evaluation benchmarks. | Not started |
| **M5** | Supervised research agents, human-in-the-loop, under explicit authorisation. | Not started |

Full plan and gating conditions: [docs/milestones/ROADMAP.md](docs/milestones/ROADMAP.md).

---

## Licensing

Scriptura has a **two-tier licence model**, and conflating the tiers is a compliance error.

**Tier 1 — Scriptura's own code and specifications.** Licensed under the
[Apache License, Version 2.0](LICENSE). See [NOTICE](NOTICE) for attribution records.

**Tier 2 — third-party corpus data.** Governed **per dataset**, by whatever licence the rights holder applied.
This is not optional and not negotiable. There is no blanket licence covering biblical data. Several upstream
sources that Scriptura intends to evaluate are explicitly licensed **per item** rather than per collection — one
such source states plainly that "each text is licensed separately, so there is no overall license". An
aggregator-level licence therefore never establishes the rights for any individual text.

The authoritative record is [docs/data/licence-manifest.json](docs/data/licence-manifest.json), cross-referenced
against [docs/data/source-registry.json](docs/data/source-registry.json). Both are validated against JSON Schema
in CI.

Every registry entry carries a `verification_status` field. **No dataset may be ingested until its licence has
been verified against a primary source and its status is `verified`.** Entries currently marked `unverified`
are candidate sources under evaluation and confer no rights whatsoever.

Details: [docs/data/README.md](docs/data/README.md) and [.clinerules/050-data-licensing.md](.clinerules/050-data-licensing.md).

---

## Relationship with Gomine

Scriptura is designed to **operate independently** while remaining **interoperable with Gomine**.

Independence is the primary property: Scriptura must be fully functional — ingest, store, query, verify, report —
with no Gomine instance present, no Gomine network dependency, and no Gomine schema assumption baked into its
storage layer. A Scriptura deployment that requires Gomine is a defective deployment.

Interoperability is achieved at the boundary, not in the core:

- **Stable identifiers.** Scriptura mints and preserves its own identifiers, and records external identifiers as
  *mappings* rather than adopting them as primary keys.
- **Exchange format.** Interop happens through explicit, versioned, serialisable exchange documents — never
  through shared database access.
- **No shared mutable state.** Scriptura never writes to a Gomine store, and never treats a Gomine store as
  authoritative for its own records.
- **Layer preservation across the boundary.** Epistemic layer typing must survive serialisation in both
  directions. An exchange format that loses layer information is rejected.

Specified in [BKB-ARCH-001 §10](docs/architecture/BKB-ARCH-001-system-architecture.md).

---

## Governance

| Document | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Binding operating contract for AI agents working in this repository |
| [.clinerules/](.clinerules/README.md) | Persistent project rules: governance, source integrity, research standards, engineering |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute; code and documentation standards; review requirements |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting; data-integrity and provenance incident handling |
| [GOVERNANCE.md](GOVERNANCE.md) | Decision rights, specification change control, roles |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [CHANGELOG.md](CHANGELOG.md) | Release and milestone history |

---

## Research integrity

Scriptura is a research instrument, and it is held to research standards rather than to product standards.
Contributions that advance capability at the cost of provenance are rejected.

- Every factual claim must resolve to a **citation of a named source**, not to a model's recollection.
- **Contested readings are preserved as competing analyses**, not resolved by preference.
- **Negative and null results are recorded.** Absence of evidence is recorded as absence, never as evidence of absence.
- **Uncertainty is represented**, not hidden. A confidence value is mandatory on derived claims.
- **Fabrication is a release-blocking defect.** A plausible-looking citation that cannot be resolved to a source is worse than a gap.

Full standards: [docs/research/methodology.md](docs/research/methodology.md) and
[.clinerules/030-research-standards.md](.clinerules/030-research-standards.md).

---

## Disclaimer

Scriptura is provided on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

Scriptura is research infrastructure. It is not a confessional statement, not a teaching authority, and not an
endorsement of any text, tradition, translation, or interpretation it contains. Inclusion of material indicates
that the material exists and is attributable — nothing more. Canon boundaries, theological positions, and
interpretive traditions vary across communities; Scriptura records these differences rather than adjudicating them.

Nothing produced by `ai_hypothesis` layer tooling should be relied upon as an authoritative statement about
scripture, history, or language.

---

## Getting help

- Questions and discussion: open a [GitHub issue](https://github.com/dhehiel/scriptura/issues).
- Bugs: use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).
- Proposing a dataset: use the [dataset addition template](.github/ISSUE_TEMPLATE/dataset_addition.yml). Licence evidence is required.
- Proposing an architecture change: use the [architecture decision template](.github/ISSUE_TEMPLATE/architecture_decision.yml).
- Security or data-integrity concerns: see [SECURITY.md](SECURITY.md). **Do not open a public issue.**
