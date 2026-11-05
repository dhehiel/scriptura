# 040 — Engineering Rules

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

---

## 1. Technology baseline

| Concern | Baseline | Change requires |
|---|---|---|
| Language | Python 3.11+ | Accepted ADR |
| Primary store | SQLite (single file) | Accepted ADR |
| Lexical search | SQLite FTS5, `unicode61`, diacritic folding | Accepted ADR |
| Knowledge graph | Modular typed nodes/edges in SQLite tables | Accepted ADR |
| Semantic retrieval | Optional LEANN adapter, import-guarded | Accepted ADR |
| HTTP surface | stdlib `http.server`, read-only, loopback | Accepted ADR |
| FastAPI | **Not adopted.** Gated. | Accepted ADR (ADR-0004) |
| Graph database | **Not present. Prohibited.** | Accepted ADR (ADR-0005) |
| Microservices | **None. Prohibited.** | Accepted ADR |

## 2. Dependency rules

1. **Zero mandatory third-party runtime dependencies at M0.** Stdlib only. Enforced by
   `tests/test_dependency_hygiene.py`.
2. **Adding a mandatory dependency requires an accepted ADR** covering: necessity, why stdlib is insufficient,
   licence compatibility with Apache 2.0, maintenance status, supply-chain assessment, and a removal path.
3. **Optional dependencies must be import-guarded.** A missing optional dependency must never raise at import
   time. Detect via a capability probe; degrade gracefully; report the degraded mode.
4. **Pin versions in CI.**
5. **No dependency whose licence is incompatible with Apache 2.0** without explicit legal review.
6. **Corpus data is never a dependency.** It never appears in `pyproject.toml`.
7. **Prohibited entirely:** `pickle`, `eval`, `exec`, `marshal`, `ctypes`-based dynamic loading, and dynamic
   code generation from data. Deserialisation is stdlib JSON only.

## 3. Module structure

```
src/scriptura/
├── core/         references, layers, hashing, errors — no I/O beyond hashing
├── storage/      SQLite connection management, migrations
├── graph/        modular knowledge graph
├── search/       FTS5 lexical search
├── retrieval/    optional semantic retrieval adapters + router
├── ingestion/    licence-gated ingestion framework and adapters
├── provenance/   licence manifest and source registry enforcement
├── schemas/      JSON Schema subset validator
└── api/          read-only HTTP surface
```

Rules:

1. **One concern per module.** No catch-all `utils` modules.
2. **Dependencies point inward.** `core` depends on nothing else in the package. `storage` may depend on `core`.
   `api` may depend on everything. Nothing depends on `api`.
3. **No circular imports.** Enforced by the import-direction test.
4. **Public API is what a package `__init__.py` exports.**
5. **`core` performs no network I/O and no database I/O.**

## 4. Code standards

1. Type hints on all public functions. `from __future__ import annotations` where useful.
2. Docstrings on public API. Reference the governing specification where one applies.
3. Errors derive from `scriptura.core.errors.ScripturaError`. Never raise bare `Exception`.
4. Explicit failure. Fail loudly with a specific error rather than returning a plausible default.
5. No silent defaults for anything semantically significant — especially **epistemic layer**.
6. No mutable default arguments.
7. Prefer pure functions; isolate I/O at module boundaries.
8. No new conventions in drive-by changes.
9. `ruff` and `mypy` are configured in `pyproject.toml`. Advisory at M0; gating once available in CI.

## 5. Data and schema rules

1. **Every schema change updates the JSON Schema** under `schemas/` in the same change.
2. **Migrations are additive and forward-only.**
   - Never edit an applied migration.
   - Add a new migration with a higher sequence number.
   - Every migration is idempotent-safe and runs inside a transaction.
   - The applied-migrations ledger records what ran, when, and the file hash.
3. **Every claim-bearing record carries an epistemic layer.** No exceptions.
4. **Every persisted record carries provenance.** No orphan records.
5. **Provenance is append-only.**
6. **Foreign keys are enforced.** `PRAGMA foreign_keys = ON` on every connection.
7. **Identifiers:** Scriptura mints its own stable identifiers. External identifiers are stored as *mappings*,
   never adopted as primary keys.
8. **Unicode:** store UTF-8. Record the normalisation form for original-language text. Do not silently
   normalise.

## 6. Testing rules

1. **Every behaviour change requires a test.** No exceptions at review.
2. **Tests run under stdlib `unittest` AND under `pytest`.** Do not use pytest-only features that break
   `python -m unittest discover`.
3. **No network access in tests.** Network-dependent tests must skip, not fail, when offline.
4. **No writes outside a temporary directory.** Use `tempfile`.
5. **Negative tests are mandatory for every validator.** What it rejects is as important as what it accepts.
6. **Round-trip tests** for every serialisation boundary, including layer preservation.
7. **Deterministic tests.** No reliance on wall-clock ordering, filesystem ordering, or dict ordering.
8. **Repository invariants are tested,** not just checked: no corpus data present, no mandatory deps, no
   prohibited imports, required documents present.

Run: `make test` and `make check`. Both must pass.

## 7. Documentation rules

1. Markdown, GitHub-flavoured. Wrap prose near 100 columns.
2. Every document has a title and a one-line purpose statement. Specifications add a status line.
3. Relative links for in-repository targets. `make check-docs` validates that every relative link resolves.
4. **Never state a licence, availability, or citation without a source.** Documentation is subject to
   [010-source-integrity.md](010-source-integrity.md).
5. Specifications carry an ID, a status, and a change history.
6. Documentation is delivered **with** the change, not after it.

## 8. Repository hygiene

1. **No corpus data in version control.** `datasets/raw|interim|processed` are gitignored landing zones.
2. **No database files, build artefacts, caches, or virtual environments committed.**
3. **No secrets.** Scriptura has no legitimate need for credentials.
4. **`.gitkeep` files** preserve empty directories that are structurally required.
5. **No large binaries.** Retrieval is a separate human-invoked step.

## 9. Reporting honesty

1. **Never claim unperformed work.** A task is complete only if performed **and verified**.
2. Where work is partial, blocked, or skipped, say so precisely: what remains, and why.
3. Include the verification evidence: commands run and their results.
4. **Do not report a check as passing without running it.**
5. **Do not report a file as created without confirming it exists.**

Claiming unperformed work is a release-blocking defect.

## 10. Definition of done

All must hold:

1. The change was made and the files exist on disk.
2. `make check` passes.
3. `make test` passes, run in this environment.
4. Affected specifications updated, or an ADR opened explaining why not.
5. Any dataset touched has a `verified` licence entry — or no dataset was touched.
6. Nothing claimed that was not performed.
7. Limitations, assumptions, and remaining work stated explicitly.

If any condition fails, report the work as **incomplete**.

## 11. Review standards **[human review]**

Reviewers check specifically for:

- provenance completeness
- layer correctness
- licence accuracy against the primary source
- absence of fabricated citations or identifiers
- absence of new mandatory dependencies
- absence of new services, brokers, or graph databases
- negative tests for new validators
- documentation delivered with the change

---

**Related:** [000-project-governance.md](000-project-governance.md) ·
[050-data-licensing.md](050-data-licensing.md) ·
[070-decision-log-protocol.md](070-decision-log-protocol.md) ·
[../CONTRIBUTING.md](../CONTRIBUTING.md) ·
[../docs/architecture/BKB-ARCH-001-system-architecture.md](../docs/architecture/BKB-ARCH-001-system-architecture.md)
