# ADR-0002 — Stdlib-only runtime at M0

| Field | Value |
|---|---|
| **ID** | ADR-0002 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §4, §11; all modules; NOTICE §3 |
| **Supersedes** | — |

## Context

Every mandatory dependency is a permanent addition to the supply-chain surface, the licence surface, and the
upgrade surface of the project. For a research infrastructure intended to remain usable for decades, each one is
a long-term liability.

An additional, concrete constraint was observed while establishing M0: **package-index access is not available in
the reference build environment.** `pip install` fails at TLS verification against `pypi.org`. Any design that
requires a third-party package to run cannot be verified in that environment, which means its claims cannot be
checked rather than assumed.

The work M0 actually requires — references, layer typing, SQLite access, FTS5 search, JSON Schema validation, a
read-only HTTP surface — is all achievable with the Python standard library.

## Decision

**The Scriptura runtime has zero mandatory third-party Python dependencies at M0.** The package depends only on
the Python standard library and on SQLite as provided by the platform.

Specifically:

1. No third-party import may appear on any runtime code path.
2. Optional integrations (`leann`, `fastapi`) are import-guarded behind capability probes and degrade gracefully.
   A missing optional dependency must never raise at import time.
3. Development and CI tooling (`pytest`, `ruff`, `mypy`) is declared as an optional extra only. It is never
   imported by runtime code.
4. Tests must run under stdlib `unittest` so that verification does not depend on an installable test runner.
5. JSON Schema validation is implemented as a stdlib validator covering the subset of JSON Schema the project
   uses. Schema documents remain standard JSON Schema for external tooling.
6. Adding a mandatory dependency requires an accepted ADR covering necessity, why stdlib is insufficient, licence
   compatibility with Apache 2.0, maintenance status, supply-chain assessment, and a removal path.

## Rationale

1. **Supply-chain risk is eliminated, not managed.** With no dependencies there is no dependency to compromise.
2. **Licence surface is eliminated.** No dependency licence to reconcile with Apache 2.0.
3. **Verifiability.** The whole system can be built, tested, and checked in an environment with no package-index
   access. Claims about the system can be demonstrated rather than asserted.
4. **Durability.** Stdlib APIs are stable across decades. Third-party APIs are not.
5. **Sufficiency.** `sqlite3`, `json`, `hashlib`, `http.server`, `argparse`, `dataclasses`, `enum`, `re`,
   `unicodedata`, and `unittest` cover everything M0 requires.
6. **Honesty about constraints.** Declaring a dependency that cannot be installed would mean shipping
   unverified code paths.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **PyYAML for registry files** | Would make the registries unreadable by the validator in this environment. Resolved instead by ADR-0003 (JSON registries). |
| **jsonschema for schema validation** | Would make schema conformance unverifiable here. A stdlib subset validator achieves the same enforcement and keeps the schema documents standard. |
| **pytest as the only runner** | Would make the test suite unrunnable here. stdlib `unittest` runs it; pytest compatibility is preserved for contributors who have it. |
| **FastAPI for the HTTP surface** | Not justified at M0. Resolved by ADR-0004. |
| **Accept the constraint and skip verification** | Rejected. Unverifiable claims violate the project's own source-integrity rules. |

## Consequences

### Positive

- No supply-chain exposure at M0.
- No dependency licence reconciliation.
- Full verification possible with no package-index access.
- Trivial installation: clone and run.

### Negative

- Some ergonomics are given up: no `pydantic` models, no `attrs`, no `rich` output, no `httpx`.
- The JSON Schema validator covers a subset, not the full specification. Mitigated: the subset is documented and
  tested; full JSON Schema documents remain valid for external tooling.
- Contributors with `pytest` installed must not write pytest-only tests. Enforced by the test rules.

### Neutral

- `ruff` and `mypy` are configured but advisory at M0, because they are not installable in the reference
  environment. They become gating once available in CI.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/040-engineering.md` | §2 dependency rules |
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §11 constraint C1 |
| `NOTICE` | §3 third-party software dependencies |
| `pyproject.toml` | No `dependencies`; extras only |
| `tests/test_dependency_hygiene.py` | Enforces |

## Verification

| Check | Command |
|---|---|
| No third-party runtime import | `python -m unittest tests.test_dependency_hygiene` |
| No prohibited imports (`pickle`, `eval`, `exec`, `marshal`) | `python -m unittest tests.test_dependency_hygiene` |
| Optional deps degrade gracefully | `python -m unittest tests.test_retrieval` |
| Tests run without pytest | `make test` |

## Related

ADR-0003, ADR-0004, ADR-0006, BKB-ARCH-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
