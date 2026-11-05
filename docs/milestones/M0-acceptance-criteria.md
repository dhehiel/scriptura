# M0 Acceptance Criteria

**Milestone M0 — Architecture Foundation**

| Field | Value |
|---|---|
| **Milestone** | M0 |
| **Status** | Criteria met; **architecture review outstanding** |
| **Gate** | M0 → M1 **CLOSED** |
| **Corpus data** | **None.** Prohibited at M0. |

## How to read this document

Milestones in Scriptura are **gated, not scheduled**. A milestone closes when its exit criteria are met **and
evidenced**, not when the work looks finished.

Every criterion below names the command or artefact that demonstrates it. A criterion without evidence is not
met. Run:

```bash
make check && make test
```

---

## A. Foundational documentation

| # | Criterion | Evidence | Status |
|---|---|---|---|
| A1 | `README.md` exists and states project purpose, layer model, technology architecture, milestone status, two-tier licensing, and Gomine interoperability | `README.md`; `make check` verifies presence | Met |
| A2 | `AGENTS.md` exists and is binding: anti-fabrication rule, layer discipline, source integrity, licence obligations, engineering obligations, autonomy boundaries, definition of done | `AGENTS.md` §1–§10 | Met |
| A3 | `CONTRIBUTING.md` exists with contribution process, dataset proposal requirements including mandatory licence evidence, code and documentation standards, and a review matrix | `CONTRIBUTING.md` | Met |
| A4 | `SECURITY.md` exists with reporting channels, a severity model treating data-integrity defects independently, and an incident process | `SECURITY.md` | Met |
| A5 | `NOTICE` exists and separates Scriptura's own work from third-party corpus data, stating explicitly that no corpus data is present | `NOTICE` §1–§5 | Met |
| A6 | `LICENSE` is the canonical Apache License, Version 2.0 | `LICENSE`; `make check` verifies the canonical header, all nine sections, and the appendix | Met |
| A7 | Governance and conduct documents exist | `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md` | Met |

## B. Persistent governance rules — `.clinerules/`

| # | Criterion | Evidence | Status |
|---|---|---|---|
| B1 | `.clinerules/` exists with an index stating precedence and enforcement | `.clinerules/README.md` | Met |
| B2 | Project governance rules: mission, scope, non-goals, decision rights, milestone gating | `.clinerules/000-project-governance.md` | Met |
| B3 | Source integrity rules: citation, quotation, provenance, anti-fabrication | `.clinerules/010-source-integrity.md` | Met |
| B4 | Epistemic layer rules with ten invariants | `.clinerules/020-epistemic-layers.md` | Met |
| B5 | Research standards: methodology, uncertainty, disagreement, null results | `.clinerules/030-research-standards.md` | Met |
| B6 | Engineering rules: code, tests, migrations, dependencies, review | `.clinerules/040-engineering.md` | Met |
| B7 | Data licensing rules with the ten-condition ingestion gate | `.clinerules/050-data-licensing.md` | Met |
| B8 | Agent safety rules with grantable and non-grantable capability sets | `.clinerules/060-agent-safety.md` | Met |
| B9 | Decision log protocol for ADRs and specification change control | `.clinerules/070-decision-log-protocol.md` | Met |

## C. Directory structure

| # | Criterion | Evidence | Status |
|---|---|---|---|
| C1 | Documentation tree exists | `docs/architecture/`, `docs/data/`, `docs/milestones/`, `docs/research/`, `docs/operations/` | Met |
| C2 | Dataset landing zone exists with `raw/`, `interim/`, `processed/`, `manifests/`, `third_party/`, and is gitignored for content | `datasets/`; `.gitignore`; `tests/test_repo_hygiene.py` | Met |
| C3 | Schema tree exists with `core/`, `data/`, `agents/`, `verification/` | `schemas/` | Met |
| C4 | Source tree exists with `core/`, `storage/`, `graph/`, `search/`, `retrieval/`, `ingestion/`, `provenance/`, `schemas/`, `api/` | `src/scriptura/` | Met |
| C5 | Research agent tree exists with `specs/`, `runs/`, `prompts/` and contains **no executable agent** | `agents/`; `tests/test_agents_absent.py` | Met |
| C6 | Ingestion pipeline tree exists with framework and adapter contract, and **no implemented adapter** | `src/scriptura/ingestion/`; `tests/test_ingestion.py` | Met |
| C7 | Evaluation and test trees exist | `evaluation/`, `tests/` | Met |
| C8 | Required structure is machine-checked, not merely present | `tools/check_repo.py`; `make check` | Met |

## D. Architecture specifications

| # | Criterion | Evidence | Status |
|---|---|---|---|
| D1 | **BKB-ARCH-001** System Architecture: decomposition, process model, module boundaries, deployment, Gomine interoperability | `docs/architecture/BKB-ARCH-001-system-architecture.md` | Met |
| D2 | **BKB-DATA-001** Data Model and Epistemic Layers: five layers, references, provenance, relational schema, invariants | `docs/architecture/BKB-DATA-001-data-model.md` | Met |
| D3 | **BKB-CORPUS-001** Corpus Ingestion: lifecycle, licence gate, adapter contract, validation, provenance | `docs/architecture/BKB-CORPUS-001-corpus-ingestion.md` | Met |
| D4 | **BKB-AGENTS-001** Research Agent Framework: contracts, capability boundaries, evidence obligations, human review. **Specified, not implemented.** | `docs/architecture/BKB-AGENTS-001-agent-framework.md` §2 | Met |
| D5 | **BKB-VERIFY-001** Verification Framework: states, evidence chains, confidence, disagreement, checks, assertion rules | `docs/architecture/BKB-VERIFY-001-verification-framework.md` | Met |
| D6 | **DKF-ARCH-001** Discovery and Knowledge Framework: hypothesis lifecycle, strategies, cross-domain linking, ranking, integrity | `docs/architecture/DKF-ARCH-001-discovery-framework.md` | Met |
| D7 | Each specification carries ID, status, version, normative flag, and change history | Verified by `tools/check_docs.py` | Met |
| D8 | Specification index and identifier convention documented | `docs/architecture/README.md` | Met |
| D9 | Architecture Decision Records exist with a mandatory "Alternatives considered" section | `docs/architecture/ADR/` — ADR-0001 … ADR-0010 | Met |

## E. Dataset governance

| # | Criterion | Evidence | Status |
|---|---|---|---|
| E1 | Dataset source registry exists, is JSON, and is schema-validated | `docs/data/source-registry.json`; `tests/test_schemas.py` | Met |
| E2 | Licence manifest exists, is JSON, and is schema-validated | `docs/data/licence-manifest.json`; `tests/test_schemas.py` | Met |
| E3 | Every entry carries an explicit `verification_status` distinguishing verified from unverified | `make check-licences` | Met |
| E4 | No licence is asserted without a primary source, and no availability is fabricated | Registry `evidence_kind` field; `make check-licences` enforces `verified` ⇒ `evidence_kind == primary` | Met |
| E5 | Verbatim attribution strings recorded where licences require them | `docs/data/attribution/ATTRIBUTIONS.md` | Met |
| E6 | **No dataset is ingestible at M0**, because the ingestion gate is closed | `ingestion_gate_open: false`; `ingestible: false` for all 27 entries; `make check-licences` | Met |
| E7 | Registry and manifest are mutually consistent | `make check-licences` | Met |

## F. Technology architecture

| # | Criterion | Evidence | Status |
|---|---|---|---|
| F1 | Python 3.11+ baseline declared | `pyproject.toml` | Met |
| F2 | SQLite is the primary store; connection management, pragmas, and a capability probe exist | `src/scriptura/storage/sqlite.py`; `tests/test_storage.py` | Met |
| F3 | SQLite FTS5 is the primary lexical search, with `unicode61` and diacritic folding; stored text is never mutated by folding | `src/scriptura/search/fts.py`; `tests/test_fts.py` | Met |
| F4 | Modular knowledge graph implemented in SQLite with layer typing and provenance; **no graph database** | `src/scriptura/graph/`; `tests/test_graph.py`; ADR-0005 | Met |
| F5 | Optional LEANN semantic retrieval adapter, import-guarded, degrading gracefully | `src/scriptura/retrieval/leann_adapter.py`; `tests/test_retrieval.py` | Met |
| F6 | FastAPI is **not adopted**; the baseline HTTP surface is stdlib, read-only, loopback-bound | `src/scriptura/api/`; `tests/test_api.py`; ADR-0004 | Met |
| F7 | **Zero mandatory third-party runtime dependencies** | `pyproject.toml` has no `dependencies`; `tests/test_dependency_hygiene.py` | Met |
| F8 | Each technology choice is recorded in an ADR | ADR-0001, 0002, 0004, 0005, 0006, 0007, 0009 | Met |

## G. Critical constraints honoured

| # | Constraint | Evidence | Status |
|---|---|---|---|
| G1 | No full Bible datasets downloaded or committed | `tests/test_repo_hygiene.py`; `make check` scans for corpus bytes | Met |
| G2 | No fabricated source availability or licensing | Registry `evidence_kind` and `verification_status`; failed fetches recorded as results | Met |
| G3 | No autonomous agents implemented | `tests/test_agents_absent.py`; `agents/specs/` contains no runnable code | Met |
| G4 | No unnecessary microservices | Single process; `tests/test_dependency_hygiene.py`; ADR-0005 | Met |
| G5 | No independent graph database introduced | `tests/test_dependency_hygiene.py`; ADR-0005 | Met |
| G6 | Scripture / historical evidence / linguistic observation / theological interpretation / AI hypothesis remain distinct | `src/scriptura/core/layers.py`; SQL `CHECK` constraints; `tests/test_layers.py` | Met |
| G7 | Scriptura operates independently while remaining interoperable with Gomine | `tests/test_independence.py`; BKB-ARCH-001 §10 | Met |
| G8 | Third-party corpus licensing treated as dataset-specific | Registry `licensing_model` field; per-item regimes recorded | Met |

## H. Verification

| # | Criterion | Evidence | Status |
|---|---|---|---|
| H1 | Repository structure and hygiene checks pass | `make check` | Met |
| H2 | Licence and registry consistency checks pass | `make check-licences` | Met |
| H3 | Documentation integrity checks pass: required files present, relative links resolve, specifications well-formed | `make check-docs` | Met |
| H4 | Full test suite passes under stdlib `unittest` | `make test` | Met |
| H5 | CI workflow runs the same checks | `.github/workflows/ci.yml` | Met |
| H6 | No task is reported complete that was not performed and verified | `M0-IMPLEMENTATION-REPORT.md` | Met |

## I. Gate criterion — **NOT MET**

| # | Criterion | Evidence | Status |
|---|---|---|---|
| **I1** | **Architecture review completed by a human reviewer, recorded with identity and date** | — | **NOT MET** |

> [!IMPORTANT]
> **This criterion cannot be satisfied by CI, by an agent, or by self-attestation.**
>
> It requires a human reviewer to read the six specifications and record approval, with identity and date, in
> this document. Until it is recorded, the M0 → M1 gate remains **CLOSED** and no corpus ingestion may occur,
> regardless of how ready the ingestion code appears.
>
> Readiness is not authorisation.

### Review record

*To be completed by the reviewer.*

| Field | Value |
|---|---|
| Reviewer | *(not recorded)* |
| Date | *(not recorded)* |
| Specifications reviewed | BKB-ARCH-001, BKB-DATA-001, BKB-CORPUS-001, BKB-AGENTS-001, BKB-VERIFY-001, DKF-ARCH-001 |
| Decision | *(pending)* |
| Conditions or required changes | *(pending)* |

---

## M0 outcome

| Item | Value |
|---|---|
| Criteria A–H | **Met**, with evidence |
| Criterion I1 | **Not met** — requires human architecture review |
| Milestone status | **Complete pending architecture review** |
| M0 → M1 gate | **CLOSED** |
| Corpus ingestion | **Prohibited** |
| Next action | Human architecture review of the six specifications |

---

## Reproducing the evidence

```bash
export PYTHONPATH=src
make check          # structure, hygiene, licences, documentation integrity, schemas
make test           # full test suite under stdlib unittest
```

Both must exit zero. Their output is recorded in
[M0-IMPLEMENTATION-REPORT.md](../../M0-IMPLEMENTATION-REPORT.md).
