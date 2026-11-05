# Operations

Build, verification, database, and deployment operations for Scriptura.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11 or newer | Standard library only. No third-party runtime dependency. |
| SQLite with FTS5 and JSON1 | Provided by the platform. Verified by the capability probe. |

Check your platform:

```bash
export PYTHONPATH=src
python3 -c "from scriptura.storage.sqlite import capability_report; print(capability_report())"
```

The probe reports the SQLite version, whether FTS5 is compiled in, whether JSON1 is functional, and whether the
`unicode61` tokenizer with diacritic folding is available. It fails loudly if a required capability is missing.

---

## Setup

```bash
git clone https://github.com/dhehiel/scriptura.git
cd scriptura
export PYTHONPATH=src
```

No install step is required. Optional development extras:

```bash
pip install -e ".[dev]"     # pytest, ruff, mypy — optional
```

---

## Verification

```bash
make check          # all repository checks
make test           # full test suite (stdlib unittest)
make check-docs     # documentation integrity only
make check-licences # licence gate and registry consistency only
make check-schemas  # schema validity only
```

`make check` runs, in order:

| Check | What it verifies |
|---|---|
| Structure | Every required file and directory exists |
| Repository hygiene | No corpus bytes, no database files, no committed artefacts |
| Dependency hygiene | No mandatory third-party runtime dependency; no prohibited imports |
| Licence gate | Registry ↔ manifest consistency; no ingestible dataset while the gate is closed |
| Documentation integrity | Required documents present; every relative link resolves; specifications well-formed |
| Schema validity | Every JSON Schema parses and is self-consistent; registries conform |
| Agent absence | No executable agent code exists |

Both `make check` and `make test` must exit zero before work is reported complete.

---

## Database operations

### Create an empty knowledge base

```bash
python3 tools/build_db.py --db /tmp/scriptura.db
```

This creates the file, applies all forward migrations, seeds the book registry and canon profiles, and reports
the resulting schema version. It writes no corpus data.

### Inspect

```bash
python3 -m scriptura.api.server --db /tmp/scriptura.db --describe
```

### Migrations

Migrations are **additive and forward-only**. They live in `src/scriptura/storage/migrations/` and are recorded
in the `schema_migrations` ledger with sequence, name, timestamp, and the SHA-256 of the file.

| Rule | Detail |
|---|---|
| Never edit an applied migration | Add a new one with a higher sequence number |
| Hash mismatch is a Critical integrity incident | It indicates an edited migration |
| Re-applying an applied migration is a no-op | Not an error |
| No down-migrations | Reversal is by a new forward migration |
| Destructive migrations require an ADR | And maintainer approval |

### Backup

The knowledge base is a single file. Back it up by copying it, or by using SQLite's online backup API for a
consistent snapshot while in use. Record the SHA-256 of any archival snapshot.

---

## Serving

The HTTP surface is **read-only** and binds to **loopback by default**.

```bash
python3 -m scriptura.api.server --db /tmp/scriptura.db --port 8765
```

| Rule | Detail |
|---|---|
| Read-only | No write endpoints exist |
| Loopback by default | Binding elsewhere requires explicit operator action |
| No authentication surface at M0 | Because it is not exposed beyond loopback. Exposing it requires an ADR covering authentication |
| FastAPI is not adopted | See [../architecture/ADR/ADR-0004-fastapi-adoption-gate.md](../architecture/ADR/ADR-0004-fastapi-adoption-gate.md) |

Do not expose this surface to a network without an approved ADR.

---

## Optional components

| Component | Effect when present | Effect when absent |
|---|---|---|
| `leann` | Enables the semantic retrieval backend | Retrieval degrades to FTS5. **Not an error.** |
| `fastapi` | Enables the optional FastAPI surface | The stdlib surface is used. **Not an error.** |

A missing optional component must never raise at import time. The retrieval router reports which backend served
a request; results from different backends are never silently mixed.

---

## Corpus data operations

**There are none at M0.** Corpus ingestion is prohibited until the M0 → M1 gate opens.

`datasets/raw/`, `datasets/interim/`, `datasets/processed/`, and `datasets/third_party/` are gitignored landing
zones. Never place corpus bytes anywhere in the repository. `make check` fails if any are found.

When ingestion is authorised at M1, the operational procedure is specified in
[../architecture/BKB-CORPUS-001-corpus-ingestion.md](../architecture/BKB-CORPUS-001-corpus-ingestion.md) and
requires, per dataset: a `verified` licence, an open milestone gate, and recorded human authorisation.

---

## Incident response

See [../../SECURITY.md](../../SECURITY.md). Data-integrity defects — fabricated provenance, corrupted text,
misapplied licences, silently collapsed epistemic layers — are security incidents and are reported through the
same private channel.

Response order: **stop the path → identify the blast radius → preserve the audit trail → notify downstream →
add a regression test and a `make check` rule.**

---

## What Scriptura does not need

Recorded so that nobody adds it:

- No server process
- No credentials
- No message broker or queue
- No worker pool or scheduler
- No container runtime
- No GPU
- No network access at runtime
- No graph database
