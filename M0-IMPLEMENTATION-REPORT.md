# M0 Implementation Report

**Milestone M0 — Architecture Foundation: implementation accounting.**

| Field | Value |
|---|---|
| **Branch** | `bootstrap/m0-recovery` |
| **Status** | Implementation complete **except** human architecture review (I1) |
| **M0 → M1 gate** | **CLOSED** |
| **Corpus data** | **None. Prohibited at M0.** |
| **Report discipline** | Nothing below is claimed without the command that produced it |

This report is the evidence record required by `M0-acceptance-criteria.md` H6.
Where work is partial, blocked, or deferred, it says so precisely.

---

## 1. What was built

### 1.1 Documentation and governance (all on disk, verified present)

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `NOTICE`, `LICENSE`
  (canonical Apache 2.0), `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.
- `.clinerules/` — 9 files: README + rules 000, 010, 020, 030, 040, 050, 060, 070.
- Six specifications: BKB-ARCH-001 (v1.0.0), BKB-DATA-001 (v1.0.1 — U6 corrected
  for verified folding behaviour), BKB-CORPUS-001, BKB-AGENTS-001 (specified, not
  implemented), BKB-VERIFY-001, DKF-ARCH-001.
- Ten ADRs (ADR-0001 … ADR-0010), each with mandatory Alternatives considered.
  ADR-0009 corrected this stage: FTS5 `remove_diacritics` verified Latin-only.
- Dataset governance: `source-registry.json` (27 sources), `licence-manifest.json`
  (9 licence records, 0 datasets), `attribution/ATTRIBUTIONS.md`.
- Milestones: `M0-acceptance-criteria.md` (per-criterion Met/Deferred/Blocked),
  `ROADMAP.md`, `README.md`.
- `docs/` index, `research/methodology.md`, `operations/README.md`.
- GitHub scaffolding on disk: 3 issue templates, PR template, CI workflow (the
  workflow file is **not pushed** — the push was refused without `workflows`
  permission; tracked as the single blocked infrastructure item).

### 1.2 Code (all on disk, all executed)

| Module | Status | Evidence |
|---|---|---|
| `core/reference.py` | Implemented, verified | 32 parse forms + strictness probes executed |
| `core/layers.py` | Implemented, verified | tests/test_layers.py: 9 tests pass |
| `core/text.py` | Implemented, verified | Greek/Hebrew/Latin folding probes executed |
| `core/hashing.py`, `core/errors.py` | Implemented, verified | exercised by every suite |
| `schemas/validator.py` | Implemented, verified | 12 schemas load; registries validate clean |
| `storage/sqlite.py` | Implemented, verified | capability probe passes on this platform |
| `storage/migrations.py` + `0001_bootstrap.sql` | Implemented, verified | applies cleanly; 17 tables; ledger verified |
| `storage/seeds.py` | Implemented, verified | 86 books, 6 profiles seeded |
| `graph/model.py`, `graph/queries.py` | Implemented, verified | layer typing + bounded traversal executed |
| `search/fts.py` | Implemented, verified | 10-case script matrix ALL OK (see §3) |
| `provenance/licensing.py` | Implemented, verified | 9-dataset matrix executed; gate refuses |
| `retrieval/` (interface, router, LEANN adapter) | Implemented, verified | degraded path executed; LEANN absent confirmed |
| `ingestion/` (pipeline, validators, base adapter) | Implemented, verified | synthetic fixtures only; gate refuses first |
| `api/server.py` | Implemented, verified | live server: all GET 200, POST/PUT/DELETE 405 |
| `api/fastapi_app.py` | Guarded stub, not adopted | raises per ADR-0004; not installed here |

### 1.3 Verification harness (all on disk, all run)

- `tests/` — 14 files, **108 tests, all pass** under stdlib `unittest`
  (`make test`). No pytest, no network.
- `tools/` — `check_repo.py`, `check_licences.py`, `check_docs.py`,
  `check_schemas.py`, `build_db.py`, `_gen_registry.py`.
- `Makefile` — `check`, `test`, `check-docs`, `check-licences`,
  `check-schemas`, `db`, `clean`.
- `pyproject.toml` — zero runtime `dependencies`; optional extras only.
- `.gitignore` — excludes all dataset bytes, databases, caches, agent runs.

---

## 2. Actual test and check results

### `make test`

```
Ran 108 tests in ~1.5s — OK
```

Suite composition:

| File | Tests | Covers (R3 item) |
|---|---|---|
| test_reference.py | 14 | 1–2: parsing, profiles, chapter counts, Catholic-73 fix |
| test_layers.py | 9 | 5, 9: closed set, requirements, confidence, promotion guard |
| test_text.py | 7 | 3: stripping, fold-match, no-romanization, final sigma |
| test_storage.py | 16 | 7: probe, migrations, ledger, CHECK rejections, seeds |
| test_graph.py | 10 | 8: nodes/edges, traversal, filters, bounds, rejections |
| test_fts.py | 8 | 3–4: exact/folded/prefix × Greek/Hebrew/Latin, flags |
| test_licensing.py | 9 | 6, 12: counts, consistency, gate conditions, refusal |
| test_ingestion.py | 5 | 5, 10–11: synthetic adapter, gate-first, validators |
| test_retrieval.py | 6 | 12: absent LEANN, degraded mode, pin-raises |
| test_schemas.py | 5 | schemas load, unsupported-keyword rejection, conformance |
| test_api.py | 7 | live server: 4 GETs 200, 3 write-methods 405, gate |
| test_repo_hygiene.py | 7 | no corpus bytes, no db files, no deps, no Gomine runtime |
| test_agents_absent.py | 3 | no executable specs, no autonomy patterns |
| test_module_boundaries.py | 2 | inward dependency direction |

### `make check`

| Sub-check | Result |
|---|---|
| structure (88 required files/dirs incl. this report) | PASS |
| hygiene (no corpus bytes, db files, caches; .gitkeep + READMEs only) | PASS |
| dependency hygiene (no third-party runtime imports; guarded LEANN/FastAPI only) | PASS |
| syntax + JSON validity | PASS |
| no Gomine runtime coupling (imports/calls) | PASS |
| no agent execution | PASS |
| check-licences (27 sources, 9 licences, gate closed, 0 ingestible) | PASS |
| check-docs (documents present, links resolve, specs well-formed, ADRs indexed) | PASS |
| check-schemas (12 schemas, registries conform) | PASS |

Without this report, `check-docs` and `make check` FAIL on the dangling
`M0-IMPLEMENTATION-REPORT.md` link — by design. With it, they pass.

### `make db`

`tools/build_db.py --db <path> --seeds` creates the database, applies migration
1, seeds 86 books + 6 profiles, and reports `corpus_records: 0` — empty by
design at M0.

---

## 3. Findings that changed the design (verified, not assumed)

1. **FTS5 `remove_diacritics` folds Latin only.** `Deesus` matches `Deesus`,
   but Greek `logos` (with tonos) does not match `logos` (without), and pointed
   Hebrew does not match unpointed Hebrew. The design now folds explicitly via
   `core/text.py` into separate indexed columns, with union matching.
   Corrected in: `core/text.py`, `search/fts.py`, migration note in
   `0001_bootstrap.sql`, ADR-0009, BKB-DATA-001 v1.0.1, README, BKB-ARCH-001,
   operations README, CHANGELOG.
2. **Quoted `"term"*` is not an FTS5 prefix query.** It silently matches
   nothing; the bare-token `term*` form is required. Corrected in `prefix_query`.
3. **UNINDEXED-column filters inside the FTS MATCH query silently discard all
   rows** (verified on SQLite 3.40.1 for multi-column OR prefix queries). Layer
   and edition filters are applied outside the FTS subquery. Documented in code.
4. **Greek final sigma requires symmetric normalisation** (U+03C2 → U+03C3 in
   the folded column and in folded queries) or prefix matching breaks.
   Stored text untouched.
5. **No romanization anywhere.** Latin queries never match Greek or Hebrew.
6. **Per-request SQLite connections in the HTTP server.** Sharing one connection
   across handler threads raises `ProgrammingError`; each handler opens and
   closes its own read-only connection.
7. **`references` is a SQL reserved word.** Table is `canonical_references`;
   BKB-DATA-001 §6.4 updated to match.
8. **Crosswire `TNT` is Tregelles' GNT, not the Tyndale House GNT.** Recorded
   as secondary evidence, `unverified`, with an explicit warning not to conflate.
9. **The Berean texts are public-domain (dedicated 2023-04-30), despite
   widespread CC-licence descriptions.** Recorded `verified` from the rights
   holder's terms page.
10. **First1KGreek publishes no licence** (README states none; no LICENSE at
    repo root). Recorded `unverified` — absence of a licence is not a public-domain
    statement. Third-party catalogue attributions are secondary evidence only.
11. **sqlite3 `Connection.execute` is read-only as an attribute.** Handler
    restructuring (not monkeypatching) was required for the per-request fix.

---

## 4. Dependency limitations (all verified in this environment)

| Package | Status | Consequence |
|---|---|---|
| pytest | NOT INSTALLED (no package-index access) | Suite runs under stdlib `unittest`; pytest-compatible by construction |
| PyYAML / jsonschema | NOT INSTALLED | Registries are JSON (ADR-0003); validation is the stdlib subset validator |
| leann | NOT INSTALLED (verified: `find_spec` None) | Retrieval degrades to FTS5; pin-semantic raises; adapter refuses cleanly |
| fastapi | NOT INSTALLED (verified) | Optional surface inert; stdlib server is the baseline |
| ruff / mypy | NOT INSTALLED | Configured in `pyproject.toml`; advisory at M0, not gating |

Zero mandatory runtime dependencies: `pyproject.toml` has no `dependencies`.
Enforced by `check_repo.py` + `test_repo_hygiene.py` (AST import scan of all
`src/scriptura/*.py`: only guarded `leann`/`fastapi` references in their adapter
modules, which is permitted).

---

## 5. Dataset and licensing status

- Registry: **27 sources** — 5 `verified`, 1 `disputed`, 1 `restricted`,
  7 `unverified`, 13 `absent`.
- Manifest: **9 licence records, 0 datasets.** No dataset authorised, none ingested.
- `licence_cleared`: 5 (`src-sblgnt`, `src-oshb`, `src-bsb`, `src-etcbc-bhsa`,
  `src-stepbible-data`). Clearance is NOT permission: `ingestible` is false for
  every entry; the registry gate is closed.
- Consistency: `consistency_problems()` returns empty; `check-licences` passes.
- Licence-cleared, ingestible-pending notes:
  - `src-bsb`: public-domain dedication 2023-04-30; attribution appreciated, not
    required; naming request honoured.
  - `src-oshb`: CC BY 4.0 with verbatim attribution string; WLC public-domain
    status is Open Scriptures' assertion, not independently verified.
  - `src-sblgnt`: CC BY 4.0; exact attribution wording still to be confirmed.
  - `src-etcbc-bhsa`: CC BY-NC 4.0 — **non-commercial quarantine required**;
    commercial enquiries go to the German Bible Society.
  - `src-stepbible-data`: CC BY 4.0 covers STEPBible's own data; does NOT cover
    embedded modern translations (e.g. anything embedding ESV text).
  - `src-morphgnt-sblgnt`: `disputed` — share-alike version unstated; two
    sources describe the underlying text licence differently.
- No full Bible datasets downloaded, vendored, committed, or derived — verified
  by `check_repo.py`, `test_repo_hygiene.py`, and `git ls-files` (no corpus
  paths tracked).

---

## 6. M0 acceptance criteria — individual classification

| ID | Criterion | Status | Evidence |
|---|---|---|---|
| A1–A7 | Foundational documentation | **Met** | files on disk |
| B1–B9 | Persistent governance rules | **Met** | `.clinerules/` on disk |
| C1–C4, C7–C8 | Directory structure (+ machine check) | **Met** | tree + `make check` structure pass |
| C5 | Agent tree, no executable agent | **Met** | declarative placeholder only; `test_agents_absent.py` passes |
| C6 | Ingestion framework, no implemented adapter | **Met** | pipeline + base contract; adapter test proves registry empty; only `base.py` in tree (plus test-local synthetic) |
| D1–D6 | Six specifications | **Met** | files on disk; D2 at v1.0.1 |
| D7 | Spec frontmatter | **Met** | present; `check_docs.py` validates |
| D8–D9 | Spec index + ADR alternatives | **Met** | index cross-check passes |
| E1–E7 | Dataset governance | **Met** | registries validate; gate refuses; 0 ingestible |
| F1 | Python 3.11+ baseline | **Met** | `pyproject.toml` |
| F2 | SQLite store + probe | **Met** | probe passes on this platform |
| F3 | FTS5 + explicit folding | **Met** | 10-case matrix ALL OK; stored text intact |
| F4 | Modular graph, no graph DB | **Met** | traversal executed; no graph dependency |
| F5 | Optional LEANN, import-guarded | **Met (degraded)** | absence verified; degraded path executed; pin raises |
| F6 | FastAPI not adopted; stdlib read-only surface | **Met** | live server: GETs 200, writes 405; stub raises |
| F7 | Zero mandatory runtime dependencies | **Met** | empty `dependencies`; AST scan passes |
| F8 | Technology choices in ADRs | **Met** | ADR-0001/2/4/5/6/7/9 (0009 corrected) |
| G1 | No corpus data committed | **Met** | check + tests + `git ls-files` |
| G2 | No fabricated availability/licensing | **Met** | evidence_kind + verification_status; failures recorded |
| G3 | No autonomous agents | **Met** | no runnable code; tests pass |
| G4 | No microservices | **Met** | single process; no services/queues |
| G5 | No graph database | **Met** | no dependency; AST scan passes |
| G6 | Layers distinct | **Met** | enum + SQL CHECKs + tests |
| G7 | Gomine independence | **Met** | no imports/calls; tests pass |
| G8 | Dataset-specific licensing | **Met** | per-item regimes recorded |
| H1–H5 | Verification harness (`make check`, tests, CI) | **Met*** | `make check` passes; `make test` 108 pass; CI workflow written but **not pushed** (permission) |
| H6 | Honest reporting | **Met** | this report |
| I1 | **Human architecture review** | **NOT MET** | requires reviewer identity + date |

\*H5 caveat: `.github/workflows/ci.yml` is written on disk but the push was
refused (`refusing to allow a GitHub App to create or update workflow ...
without 'workflows' permission`). CI content is specified and the same commands
run locally; the hosted workflow enablement is blocked on permissions, not on
content. This is the single blocked infrastructure item.

---

## 7. Commits and branch

Branch: `bootstrap/m0-recovery` (pushed to `origin`; remote verified as
`https://github.com/dhehiel/scriptura.git`).

| Commit | Subject |
|---|---|
| `41b6159` | M0 recovery checkpoint (WIP): bootstrap foundation, INCOMPLETE |
| `83c6b88` | R1 FTS: explicit diacritic folding on query and index sides |
| `238a53e` | R1 docs: correct FTS claims; criteria now per-item |
| `b373c9c` | R2: provenance licence gate + retrieval router/LEANN boundary |
| `d2ed705` | R2: ingestion framework, read-only API, threading fix |
| `2e77897` | R2: packaging, check tooling, seeds, GitHub scaffolding |
| `30e79c9` | R3: full unittest suite (108 tests) + checker fixes |
| *(this stage)* | R4: M0 implementation report; criteria closed out |

No merge into `main`. No M1 work. No autonomous agents.

---

## 8. Remaining failures and limitations

1. **I1 — human architecture review: NOT DONE.** Cannot be satisfied by CI, an
   agent, or self-attestation. The gate stays closed until a human reviewer
   records identity + date.
2. **CI workflow not pushed** (permissions). Content complete and reviewed;
   enablement needs `workflows` permission.
3. **ruff/mypy advisory only** (not installable here). Configs ship in
   `pyproject.toml`.
4. **LEANN/FastAPI absent** (verified). Degraded/guarded paths executed and
   tested; no integration claim is made.
5. **Registries frozen at 2026-11-05 research.** Rights holders may change
   terms; re-verification is required before any future ingestion.
6. Diagnostics: XCTest-style `verify_ledger` tamper test is structural rather
   than a true file-rewrite simulation; ledger protection itself is tested via
   the duplicate-sequence and re-apply paths.

---

## 9. Conclusion: is M0 complete?

**M0 implementation is complete; the M0 milestone is NOT complete.**

Everything implementable without a human reviewer has been implemented,
executed, and recorded: architecture, governance, schemas, registries, code,
108 passing tests, and a passing `make check`. No corpus data exists anywhere.
No agent executes. Nothing is claimed that was not performed.

The milestone closes when criterion I1 is recorded: a completed architecture
review by a human reviewer, with identity and date. Until then the M0 → M1
gate is **CLOSED** and corpus ingestion is **prohibited**.
