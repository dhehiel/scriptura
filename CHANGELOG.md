# Changelog

All notable changes to Scriptura are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Specification revisions are recorded separately in the `Change history` section of each specification, and are
cross-referenced from here.

---

## [Unreleased]

### Changed — seven-layer epistemic architecture (R5–R8, branch `architecture/seven-layer-epistemic-model`)

- **Epistemic model revised from five layers to seven** (ADR-0011, status `proposed`): added
  `textual_observation` and `scholarly_interpretation`. The universal ranking API (`LAYER_ORDER`,
  `layer_strength`, `weakest_layer`, `compose_layer`) is **removed** — layers classify the nature of a record,
  not its truth or authority. Confidence, evidence quality, provenance, verification status, disagreement,
  tradition, and attribution are independent metadata dimensions and never determine layer.
- **Derivation model** (`DerivationRecord`, `derivations` table): multi-output; every input/output record ID
  with its layer; method, actor, timestamps, tool identity; verification state with reviewer and decision
  authority; supporting evidence; preserved disagreements. Output layers are explicit and never computed;
  machine-generated non-hypothesis outputs require evidence + an auditable decision.
- **Conditional per-layer requirements**: a field inapplicable to a layer is never made mandatory for it.
- **Migration `0002_seven_layer_epistemic_model.sql`** (forward-only): widens layer `CHECK`s to seven values,
  adds nullable layer-specific columns, edge `verification_status`/`supporting_evidence`/`derivation_id`, and
  the `derivations` table. Preserves ids, values, and row counts; no silent reclassification; idempotent.
- **Graph**: `validate_edge_layer` replaces endpoint-inheritance (`derive_edge_layer`); non-`ai_hypothesis`
  edges require an authorised derivation; new kinds/relations; competing edges preserved.
- **Search**: `exact`/`folded`/`both` defined precisely (`exact` = stored-form column, tokenizer-normalized,
  NOT byte-exact); `verify_byte_exact` added for application-level byte-exact comparison; pagination bug fixed
  (filters applied after candidate fetch, so layer/edition filters no longer drop relevant results); hits carry
  provenance, verification status, and the non-authoritative flag.
- **Retrieval**: `RetrievalResult` gains `edition_source` and `verification_status` (never invented).
- **API security**: non-loopback binding is **rejected by default** (`ExternalBindingRefused` before any
  socket). External binding requires flag + security config + auth design + operator acknowledgement + an
  approved ADR; none exists, so it fails closed.
- **Licensing**: multi-licence datasets evaluated per licence — one unresolved licence blocks the dataset;
  commercial permission aggregates most-restrictively; any share-alike propagates.
- **Gomine exchange** (`exchange.py`): versioned export/import preserving all seven layers, ids and graph
  relationships, provenance and attribution, derivation chains, verification status and confidence, and
  competing interpretations — verified by `tests.test_gomine_exchange`.
- **Documentation**: ADR-0011 supersedes ADR-0008 (retained, marked superseded); `.clinerules/020` rewritten;
  BKB-DATA-001 → v1.1.0; BKB-ARCH-001/BKB-CORPUS-001/BKB-AGENTS-001/BKB-VERIFY-001/DKF-ARCH-001 reconciled;
  README/AGENTS/NOTICE updated; M0 acceptance criteria gained section J.
- **Tests**: suite grows to **146 tests, all passing** under stdlib `unittest`.

### Planned — M1 (gated, not started)

- Reference core in production use against a real edition.
- First single-edition corpus ingestion, under full provenance.
- **Blocked on:** M0 architecture review and maintainer approval of the M0→M1 gate.

---

## [0.1.0] — M0 — Architecture Foundation

> **Status: IN PROGRESS (M0 recovery).** This release section describes the target scope. Items marked
> "LANDS IN R2/R3" are explicitly NOT yet delivered. See `docs/milestones/M0-acceptance-criteria.md` for
> the per-criterion status and `M0-IMPLEMENTATION-REPORT.md` (R4) for the final accounting.

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

**Source code — `src/scriptura/` — IMPLEMENTED at M0 (R0/R1)**

- `core/reference.py` — canonical Bible references, book registry, multi-canon profiles, parsing and
  normalisation, range handling (verified by execution).
- `core/layers.py` — the five epistemic layers as an enforced enum, with attribution and flagging requirements.
- `core/hashing.py` — content hashing and provenance digests.
- `core/errors.py` — error hierarchy rooted at `ScripturaError`.
- `core/text.py` — explicit Unicode diacritic folding (`fold_diacritics`, final-sigma normalisation).
- `storage/sqlite.py` — connection management, pragmas, capability probe for FTS5 and JSON1
  (verified by execution).
- `storage/migrations.py` — forward-only migration runner with an applied-migrations ledger
  (verified by execution, including ledger hash-mismatch detection).
- `storage/migrations/0001_bootstrap.sql` — bootstrap schema (applies cleanly; 17 tables).
- `graph/model.py` — modular knowledge graph over SQLite: typed nodes and edges, layer-typed,
  provenance-bearing (verified by execution).
- `graph/queries.py` — bounded, layer-filtered graph traversal (verified by execution).
- `search/fts.py` — SQLite FTS5 wrapper with original + explicitly folded index columns. Matching is a
  union over both columns, never transliteration (VERIFIED by execution: Greek polytonic/plain/prefix,
  Hebrew pointed/unpointed/prefix, Latin accented/plain/prefix; no romanization leakage; stored
  text byte-identical).
- `schemas/validator.py` — stdlib JSON Schema subset validator (verified by execution: all schemas load,
  registries validate with zero violations, unsupported keywords raise).

**Source code — lands in R2 (NOT yet implemented)**

- `retrieval/leann_adapter.py` — optional LEANN adapter, import-guarded.
- `retrieval/router.py` — retrieval routing with capability-based backend selection.
- `ingestion/pipeline.py` — licence-gated ingestion framework.
- `ingestion/validators.py` — dataset validation rules.
- `ingestion/adapters/base.py` — adapter contract. No dataset adapters implemented at M0.
- `provenance/licensing.py` — licence manifest and source registry loading and gate enforcement.
- `api/server.py` — read-only stdlib HTTP surface.
- `api/fastapi_app.py` — optional FastAPI surface, import-guarded and gated by ADR-0004.
- `src/scriptura/__init__.py` — package entry point.

**Directory structure**

- `datasets/` — `raw/`, `interim/`, `processed/`, `manifests/`, `third_party/`. All gitignored for data.
- `agents/` — `specs/`, `runs/`, `prompts/`. Declarative specifications only.
- `evaluation/` — `benchmarks/`, `datasets/`, `reports/`.
- `tests/` — stdlib `unittest` suite, pytest-compatible (LANDS IN R2/R3).
- `tools/` — `check_repo.py`, `check_licences.py`, `check_docs.py`, `build_db.py`, `_gen_registry.py` (check tools LAND IN R2).

**Project configuration**

- `pyproject.toml` — packaging, zero mandatory runtime dependencies, optional extras (LANDS IN R2).
- `Makefile` — `check`, `test`, `check-docs`, `check-licences`, `db`, `clean` (LANDS IN R2).
- `.gitignore` — excludes all dataset bytes, databases, and local artefacts (IN PLACE).
- `.editorconfig` — editor conventions (LANDS IN R2).
- `.github/workflows/ci.yml` — CI running checks and tests (LANDS IN R2).
- `.github/ISSUE_TEMPLATE/` — bug report, dataset addition, architecture decision templates (LAND IN R2).
- `.github/PULL_REQUEST_TEMPLATE.md` — PR checklist including licence and provenance compliance (LANDS IN R2).

### Security

- Runtime has **zero mandatory third-party dependencies**, eliminating supply-chain exposure at M0.
- No network I/O on any runtime path.
- No deserialisation beyond stdlib JSON. No `pickle`, `eval`, `exec`, or dynamic code generation.
- Default HTTP surface is read-only and binds to loopback.
- Licence gate blocks ingestion of any dataset whose `verification_status` is not `verified`.

### Known limitations at M0

Recorded deliberately, not omissions. Updated during the M0 recovery (R0/R1):

- **Recovery in progress.** The R0 checkpoint commit states what is incomplete. `M0-acceptance-criteria.md`
  now classifies each criterion individually as Met, Deferred, or Blocked instead of claiming completion.
- **FTS design corrected.** FTS5 `remove_diacritics` was verified to fold Latin only; Greek and Hebrew
  folding is explicit via `core/text.py` into a separate indexed column. ADR-0009 and BKB-DATA-001 §7
  (v1.0.1) record the verified behaviour.

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
