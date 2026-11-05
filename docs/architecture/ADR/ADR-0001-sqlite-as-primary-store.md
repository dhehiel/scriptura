# ADR-0001 — SQLite as the primary store

| Field | Value |
|---|---|
| **ID** | ADR-0001 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §6, BKB-DATA-001 §6 |
| **Supersedes** | — |

## Context

Scriptura must store provenanced biblical research data: scripture text by edition, linguistic annotation,
external evidence, attributed interpretation, and machine-generated hypotheses, together with a graph of typed
relationships and full-text search over Greek, Hebrew, Latin, and English.

Constraints:

- The corpus is **bounded**. Biblical and related literature is finite, measured in gigabytes.
- Users are **researchers on workstations**, not operators of infrastructure.
- **Auditability** is a first-class requirement: a researcher must be able to inspect, hash, copy, and back up
  the entire store.
- **Durability** matters on a decades timescale. Research data outlives database products.
- The runtime must not require a server, credentials, or network.
- FTS5 and JSON1 are available in the platform SQLite (verified: SQLite 3.40.1, `ENABLE_FTS5` present, JSON1
  functional).

## Decision

**SQLite is the primary and only persistent store.** The knowledge base is a single database file.

Specifically:

1. All persistent state lives in one SQLite file.
2. `PRAGMA foreign_keys = ON` on every connection.
3. WAL journal mode where readers and a writer coexist.
4. Full-text search uses FTS5 virtual tables in the same file.
5. The knowledge graph is relational tables in the same file (see ADR-0007).
6. Migrations are forward-only and ledgered in the same file.
7. No client-server database is used at any layer.

## Rationale

1. **Auditability.** A single file can be hashed, copied, diffed, backed up, and opened with ubiquitous tooling.
   A researcher can verify the store without trusting a service.
2. **Zero operational surface.** No server process, no credentials, no listening socket, no version drift
   between client and service, no authentication to compromise.
3. **Sufficient capability.** FTS5 provides full-text indexing with `unicode61` tokenization and diacritic
   folding — exactly what Greek and Hebrew search requires. JSON1 provides structured payloads. CHECK
   constraints enforce the epistemic layer invariants at the storage level.
4. **Durability.** The SQLite file format is documented, stable, and explicitly targeted at long-term archival.
5. **Scale fit.** The workload is research queries over a bounded corpus, not high-concurrency transaction
   throughput. Distribution would add failure modes while solving no existing problem.
6. **Interoperability.** Any language with a SQLite binding can read the store, which supports the Gomine
   boundary requirement without coupling.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **PostgreSQL** | Excellent engine, but requires a server process, credentials, and a network surface. Adds operational burden and an authentication attack surface for no capability the workload needs. Researchers could not simply copy the store. |
| **DuckDB** | Strong analytical engine and columnar storage, but weaker for transactional write patterns, and FTS support is not equivalent to FTS5. Revisit if analytical workloads dominate. |
| **Plain files (JSON/Parquet) only** | Maximally durable and inspectable, but no referential integrity, no CHECK constraints, no transactions, no in-store search. Layer invariants would be unenforceable at the storage level. |
| **Document database (MongoDB, CouchDB)** | Server-based, schema-optional. Schema-optional is a liability here: the layer invariants must be enforced, not hoped for. |
| **Embedded key-value (LevelDB, RocksDB)** | No relational integrity, no SQL, no in-store full-text search. |

## Consequences

### Positive

- Zero-infrastructure deployment; the system runs on a laptop.
- Layer invariants enforceable by `CHECK` constraints.
- Full-text search co-located with data; no index synchronisation problem.
- The entire store is one hashable artefact.
- No credentials, no listening socket, no authentication surface.

### Negative

- Write concurrency is serialised. Mitigated: writes are rare (ingestion), reads dominate.
- No horizontal scale. Accepted: the corpus is bounded and no requirement demands it.
- Some analytical query patterns are slower than a columnar engine. Accepted at M0; revisit with data.
- Single-file stores can be corrupted by concurrent writers outside WAL discipline. Mitigated: WAL, one process.

### Neutral

- Platform SQLite must have FTS5 and JSON1. A capability probe checks this at startup and fails loudly.

## Compliance

| Document | Effect |
|---|---|
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §6 storage architecture |
| `docs/architecture/BKB-DATA-001-data-model.md` | §6 relational schema |
| `.clinerules/040-engineering.md` | §1 technology baseline |
| `NOTICE` | §3 records no mandatory dependency |

## Verification

| Check | Command |
|---|---|
| Capability probe detects FTS5 and JSON1 | `python -m unittest tests.test_storage` |
| Schema creation and constraints | `python -m unittest tests.test_storage` |
| Foreign keys enforced | `python -m unittest tests.test_storage` |
| Migration ledger | `python -m unittest tests.test_storage` |

## Related

ADR-0005, ADR-0007, ADR-0009, BKB-ARCH-001, BKB-DATA-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
