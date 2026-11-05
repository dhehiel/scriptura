# Changelog

All notable changes to Scriptura are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Specification revisions are recorded separately in the `Change history` section of each specification, and are
cross-referenced from here.

---

## [Unreleased]

### Planned — M1 (gated, not started)

- Reference core in production use against a real edition.
- First single-edition corpus ingestion, under full provenance.
- **Blocked on:** M0 architecture review and maintainer approval of the M0→M1 gate.

---

## [0.1.0] — M0 — Architecture Foundation

Initial bootstrap of the repository. Establishes architecture, governance, schemas, and infrastructure
scaffolding. **Contains no corpus data and implements no autonomous agents.**

### Added

**Project documentation and governance**

- `README.md` — project overview, layer model, technology architecture, milestone status, two-tier licensing,
  Gomine interoperability statement.
- `AGENTS.md` — binding operating contract for AI agents: anti-fabrication rule, layer discipline, source
  integrity, licence obligations, engineering obligations, autonomy boundaries, definition of done.
- `CONTRIBUTING.md` — contribution process, dataset proposal requirements including mandatory licence evidence,
  code and documentation standards, review matrix.
- `SECURITY.md` — vulnerability reporting, four-level severity model with independent data-integrity severity,
  data-integrity incident process, M0 security posture.
- `NOTICE` — Apache 2.0 attribution record, two-tier scope separation, explicit statement that no third-party
  corpus data is present at M0.
- `GOVERNANCE.md` — principles, roles, decision rights matrix, specification change control, milestone gating.
- `CODE_OF_CONDUCT.md` — adapted from Contributor Covenant 2.1, with project-specific provisions for handling
  doctrinal and textual disagreement.
- `LICENSE` — Apache License, Version 2.0 (canonical text, 202 lines).

**Persistent governance rules — `.clinerules/`**

- `000-project-governance.md` — mission, scope, non-goals, decision rights, milestone gating.
- `010-source-integrity.md` — citation, quotation, provenance, anti-fabrication rules.
- `020-epistemic-layers.md` — the five layers, their invariants, and prohibition on promotion.
- `030-research-standards.md` — methodology, uncertainty, disagreement, null results.
- `040-engineering.md` — code, tests, migrations, dependencies, review standards.
- `050-data-licensing.md` — dataset-specific licensing, the ingestion licence gate.
- `060-agent-safety.md` — autonomy limits, capability boundaries, audit obligations.
- `070-decision-log-protocol.md` — ADR and specification change control.

**Architecture specifications — `docs/architecture/`**

- `BKB-ARCH-001` — System Architecture: decomposition, process model, module boundaries, deployment, Gomine
  interoperability.
- `BKB-DATA-001` — Data Model and Epistemic Layers: the five layers, provenance model, canonical references,
  relational schema, invariants.
- `BKB-CORPUS-001` — Corpus Ingestion: dataset lifecycle, licence gate, adapter contract, validation, provenance
  capture, rollback.
- `BKB-AGENTS-001` — Research Agent Framework: agent contracts, capability boundaries, evidence obligations,
  human review. Declarative only at M0; no execution.
- `BKB-VERIFY-001` — Verification Framework: claim verification, evidence chains, confidence, disagreement
  handling, audit.
- `DKF-ARCH-001` — Discovery and Knowledge Framework: hypothesis generation, cross-domain linking,
  hypothesis → candidate → verified lifecycle, discovery integrity.

**Architecture Decision Records — `docs/architecture/ADR/`**

- `ADR-0001` — SQLite as the primary store.
- `ADR-0002` — Stdlib-only runtime at M0.
- `ADR-0003` — JSON as the format for machine-readable registries.
- `ADR-0004` — FastAPI adoption gate.
- `ADR-0005` — No independent graph database.
- `ADR-0006` — LEANN as an optional retrieval adapter.
- `ADR-0007` — Modular knowledge graph implemented in SQLite.
- `ADR-0008` — Epistemic layer typing as a storage-level invariant.
- `ADR-0009` — SQLite FTS5 as primary lexical search.
- `ADR-0010` — Licence gate on all corpus ingestion.

**Dataset governance — `docs/data/`**

- `source-registry.json` — dataset source registry with per-source licence, availability, and an explicit
  `verification_status` distinguishing `verified` from `unverified` candidates.
- `licence-manifest.json` — machine-readable licence manifest, schema-validated, enforcing the ingestion gate.
- `attribution/ATTRIBUTIONS.md` — verbatim attribution strings required by upstream licences.
- `README.md` — dataset governance policy and the two-tier licence model.

**Milestone planning — `docs/milestones/`**

- `M0-acceptance-criteria.md` — M0 exit criteria with per-criterion evidence and verification commands.
- `ROADMAP.md` — M0–M5 milestone plan with explicit gating conditions.

**JSON Schemas — `schemas/`**

- `core/` — `reference`, `epistemic-layer`, `claim`, `evidence`, `provenance`, `edge`.
- `data/` — `dataset-manifest`, `source-registry-entry`, `licence-record`.
- `agents/` — `agent-spec`, `agent-run`.
- `verification/` — `verification-result`.

**Source code — `src/scriptura/`**

- `core/reference.py` — canonical Bible references, book registry, multi-canon profiles, parsing and
  normalisation, range handling.
- `core/layers.py` — the five epistemic layers as an enforced enum, with attribution and flagging requirements.
- `core/hashing.py` — content hashing and provenance digests.
- `core/errors.py` — error hierarchy rooted at `ScripturaError`.
- `storage/sqlite.py` — connection management, pragmas, capability probe for FTS5 and JSON1.
- `storage/migrations.py` — forward-only migration runner with an applied-migrations ledger.
- `storage/migrations/0001_bootstrap.sql` — bootstrap schema.
- `graph/model.py` — modular knowledge graph over SQLite: typed nodes and edges, layer-typed, provenance-bearing.
- `graph/queries.py` — graph traversal and layer-filtered queries.
- `search/fts.py` — SQLite FTS5 wrapper with `unicode61` tokenizer and diacritic folding.
- `retrieval/leann_adapter.py` — optional LEANN adapter, import-guarded, graceful degradation to FTS5.
- `retrieval/router.py` — retrieval routing with capability-based backend selection.
- `ingestion/pipeline.py` — licence-gated ingestion framework.
- `ingestion/validators.py` — dataset validation rules.
- `ingestion/adapters/base.py` — adapter contract. No dataset adapters implemented at M0.
- `provenance/licensing.py` — licence manifest and source registry loading and gate enforcement.
- `schemas/validator.py` — stdlib JSON Schema subset validator.
- `api/server.py` — read-only stdlib HTTP surface.
- `api/fastapi_app.py` — optional FastAPI surface, import-guarded and gated by ADR-0004.

**Directory structure**

- `datasets/` — `raw/`, `interim/`, `processed/`, `manifests/`, `third_party/`. All gitignored for data.
- `agents/` — `specs/`, `runs/`, `prompts/`. Declarative specifications only.
- `evaluation/` — `benchmarks/`, `datasets/`, `reports/`.
- `tests/` — stdlib `unittest` suite, pytest-compatible.
- `tools/` — `check_repo.py`, `check_licences.py`, `check_docs.py`, `build_db.py`.

**Project configuration**

- `pyproject.toml` — packaging, zero mandatory runtime dependencies, optional extras.
- `Makefile` — `check`, `test`, `check-docs`, `check-licences`, `db`, `clean`.
- `.gitignore` — excludes all dataset bytes, databases, and local artefacts.
- `.editorconfig` — editor conventions.
- `.github/workflows/ci.yml` — CI running checks and tests.
- `.github/ISSUE_TEMPLATE/` — bug report, dataset addition, architecture decision templates.
- `.github/PULL_REQUEST_TEMPLATE.md` — PR checklist including licence and provenance compliance.

### Security

- Runtime has **zero mandatory third-party dependencies**, eliminating supply-chain exposure at M0.
- No network I/O on any runtime path.
- No deserialisation beyond stdlib JSON. No `pickle`, `eval`, `exec`, or dynamic code generation.
- Default HTTP surface is read-only and binds to loopback.
- Licence gate blocks ingestion of any dataset whose `verification_status` is not `verified`.

### Known limitations at M0

Recorded deliberately, not omissions:

- **No corpus data.** Nothing has been ingested. Ingestion is gated on architecture review.
- **No agents execute.** `agents/specs/` contains declarative specifications only.
- **No dataset adapters implemented.** The adapter contract exists; no adapter has been written, because no
  dataset is authorised.
- **LEANN is not installed** in the reference environment. The adapter degrades to FTS5, which is the specified
  behaviour.
- **FastAPI is not installed** in the reference environment and is not adopted. The stdlib surface is the
  baseline.
- **`ruff` and `mypy` are not available** in the reference environment due to absent package-index access. They
  are declared as optional extras and are advisory, not gating, at M0.
- **Some registry entries are `unverified`.** They are candidate sources under evaluation and confer no rights.
  They may not be ingested.
- **Single maintainer.** See the governance caveat in [GOVERNANCE.md](GOVERNANCE.md).

---

## Legend

- **Added** — new features
- **Changed** — changes to existing functionality
- **Deprecated** — soon-to-be removed features
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — security and integrity changes

[Unreleased]: https://github.com/dhehiel/scriptura/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dhehiel/scriptura/releases/tag/v0.1.0
