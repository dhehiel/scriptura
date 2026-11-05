# BKB-ARCH-001 — System Architecture

**Biblical Knowledge Base — System Architecture**

| Field | Value |
|---|---|
| **ID** | BKB-ARCH-001 |
| **Status** | Accepted |
| **Version** | 1.0.0 |
| **Milestone** | M0 |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Supersedes** | — |

## Abstract

This specification defines the overall architecture of Scriptura: its design principles, logical decomposition,
process model, module boundaries and dependency direction, storage and retrieval architecture, deployment model,
extensibility points, and the boundary at which it interoperates with Gomine. It establishes the standing
constraints that make Scriptura a single-process, single-file-database research instrument rather than a
distributed system.

---

## 1. Purpose and scope

### 1.1 Purpose

Scriptura exists so that biblical research questions can be asked against provenanced data with kinds of claim
auditably separated. This specification defines the system that makes that possible.

### 1.2 In scope

- Design principles and their architectural consequences
- Logical decomposition into modules
- Process model and its prohibitions
- Module boundaries, public API, and dependency direction
- Storage architecture
- Retrieval architecture
- Deployment model
- Extensibility points
- Gomine interoperability boundary

### 1.3 Out of scope

- The data model itself — see [BKB-DATA-001](BKB-DATA-001-data-model.md)
- Ingestion lifecycle — see [BKB-CORPUS-001](BKB-CORPUS-001-corpus-ingestion.md)
- Agent contracts — see [BKB-AGENTS-001](BKB-AGENTS-001-agent-framework.md)
- Verification semantics — see [BKB-VERIFY-001](BKB-VERIFY-001-verification-framework.md)
- Discovery semantics — see [DKF-ARCH-001](DKF-ARCH-001-discovery-framework.md)

---

## 2. Design principles

These principles are normative. Where an implementation choice conflicts with a principle, the principle wins
and an ADR is required to change it.

| # | Principle | Architectural consequence |
|---|---|---|
| P1 | **Provenance precedes capability** | Every record carries provenance. No orphan records. Provenance is append-only. |
| P2 | **Epistemic layers are structural** | Layer is a storage-level invariant, not a convention. See P1 of BKB-DATA-001. |
| P3 | **One process, one database file** | No microservices, no brokers, no daemons. |
| P4 | **Stdlib-first** | Zero mandatory third-party runtime dependencies at M0. |
| P5 | **Durability over novelty** | SQLite, plain files, JSON. Formats readable in fifty years. |
| P6 | **Auditability over convenience** | Every mutation is traceable to an actor, a time, and a reason. |
| P7 | **Optional capabilities degrade gracefully** | A missing optional component never breaks correctness. |
| P8 | **Independence with interoperability** | Fully functional alone; interoperable at the boundary only. |
| P9 | **Fail loudly** | No silent defaults for semantically significant values. |
| P10 | **Laptop-scale sufficiency** | The system must be usable on a single machine without infrastructure. |

---

## 3. System context

```
                    ┌──────────────────────────────────────────────┐
                    │              External world                  │
                    │                                              │
   Human-invoked    │   Upstream dataset sources (rights holders)  │
   ingestion only   │   ── licence-verified before retrieval ──     │
                    └──────────────────┬───────────────────────────┘
                                       │  (offline by default; no runtime network I/O)
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SCRIPTURA  (single process)                          │
│                                                                              │
│   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────────────┐  │
│   │  ingestion │──▶│  storage   │◀──│   graph    │   │  search / retrieval│  │
│   │ (gated)    │   │  (SQLite)  │   │  (SQLite)  │   │  (FTS5 + optional) │  │
│   └────────────┘   └─────┬──────┘   └─────┬──────┘   └─────────┬──────────┘  │
│        ▲                 │                │                    │             │
│        │                 └────────┬───────┴────────────────────┘             │
│   licence gate                    ▼                                          │
│   (provenance)             ┌────────────┐    ┌──────────────┐                │
│                            │    api     │◀───│  evaluation  │                │
│                            │ (read-only)│    └──────────────┘                │
│                            └─────┬──────┘                                    │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   │  versioned exchange documents only
                                   ▼
                    ┌──────────────────────────────┐
                    │          Gomine              │   (never a runtime dependency)
                    └──────────────────────────────┘
```

**Key properties:**

- No runtime network I/O. Retrieval is a separate, human-invoked ingestion step.
- One process. One database file.
- The API surface is read-only.
- Gomine is reachable only through exchange documents, and is never required.

---

## 4. Logical decomposition

### 4.1 Module map

| Module | Path | Responsibility | Depends on |
|---|---|---|---|
| `core` | `src/scriptura/core/` | Canonical references, epistemic layers, hashing, error hierarchy | *(nothing)* |
| `schemas` | `src/scriptura/schemas/` | JSON Schema subset validation | `core` |
| `storage` | `src/scriptura/storage/` | SQLite connections, pragmas, capability probe, migrations | `core` |
| `provenance` | `src/scriptura/provenance/` | Source registry and licence manifest; the ingestion gate | `core`, `schemas` |
| `graph` | `src/scriptura/graph/` | Modular knowledge graph: typed nodes and edges | `core`, `storage` |
| `search` | `src/scriptura/search/` | FTS5 lexical search | `core`, `storage` |
| `retrieval` | `src/scriptura/retrieval/` | Optional semantic adapters; capability-based routing | `core`, `search` |
| `ingestion` | `src/scriptura/ingestion/` | Licence-gated ingestion framework; adapter contract | `core`, `schemas`, `storage`, `provenance` |
| `api` | `src/scriptura/api/` | Read-only HTTP surface | everything above |

### 4.2 Dependency direction

Dependencies point **inward** and are acyclic:

```
core  ◀──  schemas  ◀──  provenance
  ▲                          ▲
  │                          │
storage  ◀──────────────  ingestion
  ▲   ▲                      ▲
  │   │                      │
graph search ──▶ retrieval   │
  ▲   ▲                      │
  └───┴──────────────────────┴──── api
```

**Rules:**

1. `core` depends on nothing within the package.
2. `core` performs no database I/O and no network I/O.
3. No circular imports. Enforced by `tests/test_module_boundaries.py`.
4. Nothing depends on `api`.
5. A module's public API is what its `__init__.py` exports.

### 4.3 Why this decomposition

The boundaries follow **warrant**, not convenience:

- `core` holds the vocabulary in which everything else speaks: references, layers, identity. It is pure so it
  can be reasoned about and tested without I/O.
- `provenance` is separated from `ingestion` because the licence gate must be able to refuse ingestion, and a
  gate that lives inside the thing it gates is not a gate.
- `search` and `retrieval` are separated because lexical search is **always available** while semantic
  retrieval is **optional**. Conflating them would make an optional dependency load-bearing.
- `graph` is separated from `storage` so that the graph model can evolve without destabilising the storage
  contract.

---

## 5. Process model

### 5.1 Single process

Scriptura runs as **one process**. There is no service mesh, no message broker, no worker pool, no sidecar, no
daemon, and no coordination layer.

**Rationale:** the workload is research, not transaction throughput. The dataset scale is bounded — the corpus
of biblical and related literature is finite and measured in gigabytes, not petabytes. Distribution would add
failure modes, consistency problems, and operational burden while solving no problem that exists.

See [ADR-0005](ADR/ADR-0005-no-graph-database.md) and the standing constraint in
[.clinerules/000-project-governance.md](../../.clinerules/000-project-governance.md) §3.

### 5.2 Concurrency

- SQLite in WAL mode where a writer and readers coexist.
- Writers serialise. Readers do not block.
- Long-running analytical work runs **outside** the API process, against the same file, read-only.
- No distributed locks. No coordination. If you need them, you need an ADR.

### 5.3 Prohibition

Introducing any of the following requires an accepted ADR that first demonstrates why a single process cannot
satisfy the requirement:

- a microservice or separate deployable
- a message broker or queue
- a worker pool or task scheduler
- a separate graph database
- a caching layer as a distinct process
- any network dependency in the runtime path

---

## 6. Storage architecture

Specified in full in [BKB-DATA-001](BKB-DATA-001-data-model.md). Architecturally:

| Property | Value |
|---|---|
| Engine | SQLite |
| Topology | Single file |
| Server | None |
| Journal mode | WAL for concurrent read/write; DELETE for archival snapshots |
| Foreign keys | Enforced on every connection (`PRAGMA foreign_keys = ON`) |
| Migrations | Forward-only, additive, ledgered |
| Integrity | Content hashes on corpus records; append-only provenance |
| Search | FTS5 virtual tables, external-content where appropriate |

**Rationale:** SQLite is a single file that any researcher can open, copy, hash, back up, and inspect with
ubiquitous tooling. There is no server to compromise, no credentials to leak, no network surface, and no version
drift between a client and a service. For a research corpus of bounded size, this is strictly better than a
client-server engine. See [ADR-0001](ADR/ADR-0001-sqlite-as-primary-store.md).

---

## 7. Retrieval architecture

### 7.1 Two tiers

| Tier | Backend | Availability | Purpose |
|---|---|---|---|
| **1 — baseline** | SQLite FTS5 | Always | Lexical and morphological search; exact and diacritic-folded matching |
| **2 — optional** | LEANN adapter | Only if installed | Semantic similarity retrieval |

### 7.2 Capability-based routing

The retrieval router probes capabilities at construction and selects a backend accordingly. It **never** assumes
tier 2 is present.

```
request ──▶ router ──▶ capability probe
                          │
                          ├── leann present ──▶ semantic backend ──▶ results (layer-typed)
                          │
                          └── leann absent  ──▶ FTS5 backend     ──▶ results (layer-typed)
```

**Rules:**

1. Absence of the optional backend is **not an error**. It is a degraded mode, reported as such.
2. The router reports which backend served a request. Results are not silently mixed.
3. Results always carry epistemic layer information, regardless of backend.
4. A caller may pin a backend. Pinning an unavailable backend raises rather than silently falling back.
5. No backend may reorder or filter results in a way that drops layer information.

### 7.3 Why FTS5 is the baseline

Biblical search is dominated by lexical and morphological queries: lemma, form, phrase, and diacritic-variant
matching across Greek, Hebrew, Latin, and English. FTS5 with the `unicode61` tokenizer and diacritic folding
handles this in-database, with no additional process, no additional index format, and no additional failure
mode. Semantic retrieval is complementary, not substitutive. See
[ADR-0009](ADR/ADR-0009-fts5-primary-lexical-search.md) and
[ADR-0006](ADR/ADR-0006-leann-optional-retrieval.md).

---

## 8. Deployment model

### 8.1 Supported topologies

| Topology | Description | Supported |
|---|---|---|
| **Library** | `import scriptura` in a researcher's own code | Yes — primary |
| **CLI** | `tools/*.py` and `python -m scriptura.*` | Yes |
| **Local read-only HTTP** | `scriptura.api.server`, loopback-bound | Yes |
| **Embedded in another app** | Scriptura as a dependency of a larger system | Yes |
| **Distributed / clustered** | Multiple coordinating Scriptura instances | **No** — requires ADR |
| **Managed service** | Scriptura operated as a hosted multi-tenant service | **No** — requires ADR |

### 8.2 HTTP surface

- Read-only. No write endpoints.
- Binds to loopback by default. Binding to a non-loopback interface requires explicit operator action.
- No authentication surface at M0, because it is not exposed beyond loopback. Exposing it beyond loopback
  requires an ADR covering authentication and authorisation.
- stdlib `http.server` is the baseline. FastAPI is gated by
  [ADR-0004](ADR/ADR-0004-fastapi-adoption-gate.md).

### 8.3 Resource expectations

Scriptura targets a single workstation. It must not require a GPU, a server, or a container runtime. Where an
optional capability requires more (for example embedding generation), that capability is optional and its
requirements are documented with it.

---

## 9. Extensibility points

Scriptura is "open and extensible" through **defined seams**, not through arbitrary modification.

| Seam | Mechanism | Constraint |
|---|---|---|
| **New canon profile** | Register a profile in `core/reference.py` | Must not alter an existing profile |
| **New corpus adapter** | Implement the adapter contract in `ingestion/adapters/` | Licence gate applies; human authorisation per dataset |
| **New retrieval backend** | Implement the backend protocol in `retrieval/` | Must be optional; must preserve layers |
| **New graph edge type** | Register in the edge-type vocabulary | Must carry a layer; must be schema-updated |
| **New verification check** | Implement the check protocol | Must be deterministic and reproducible |
| **New discovery strategy** | Implement the strategy protocol | Output is always `ai_hypothesis` unless sourced |
| **New epistemic layer** | — | **Closed set.** Requires an accepted ADR |

**Rules:**

1. Extension is by **addition at a seam**, never by modification of a core invariant.
2. Every extension updates the corresponding JSON Schema.
3. Every extension ships tests, including negative tests.
4. No extension may relax a `.clinerules/` obligation.

---

## 10. Gomine interoperability

### 10.1 The two properties

Scriptura is designed to **operate independently** while remaining **interoperable with Gomine**.

**Independence is primary.** Scriptura must be fully functional — ingest, store, query, verify, report — with:

- no Gomine instance present,
- no Gomine network dependency,
- no Gomine credential,
- no Gomine schema assumption in its storage layer.

A Scriptura deployment that requires Gomine is a **defective deployment**. This is testable and tested:
`tests/test_independence.py` asserts that no module in the runtime path references Gomine.

**Interoperability is at the boundary.** It is achieved without coupling the cores.

### 10.2 Interoperability rules

| # | Rule |
|---|---|
| I1 | Scriptura mints and preserves **its own** stable identifiers. External identifiers are stored as *mappings*, never adopted as primary keys. |
| I2 | Interop occurs through **explicit, versioned, serialisable exchange documents**. Never through shared database access. |
| I3 | **No shared mutable state.** Scriptura never writes to a Gomine store and never treats a Gomine store as authoritative for its own records. |
| I4 | **Epistemic layer typing survives serialisation in both directions.** An exchange format that cannot represent layers is rejected. |
| I5 | **Provenance survives the boundary.** An exchanged record carries its provenance or is marked as lacking it. |
| I6 | **Licence information survives the boundary.** An exchanged dataset record carries its licence record. |
| I7 | Exchange documents are **versioned**. A version change is a schema change and requires an ADR. |
| I8 | Import from Gomine is subject to the same validation as any other ingestion, including the licence gate. |
| I9 | Export never emits unflagged `ai_hypothesis` content. |
| I10 | Gomine availability must never affect Scriptura correctness, latency guarantees, or test outcomes. |

### 10.3 Exchange document shape

An exchange document is a JSON object containing:

- `exchange_version` — the format version
- `direction` — `import` or `export`
- `source_system` / `target_system`
- `records` — each with identifier, layer, provenance, licence reference where applicable, and payload
- `identifier_mappings` — Scriptura identifier ↔ external identifier pairs
- `generated_at`, `generator`

Layer, provenance, and licence fields are **mandatory**. A record missing them is rejected on import and is
never emitted on export.

### 10.4 What interoperability is not

- Not a shared database.
- Not a shared schema.
- Not a runtime dependency.
- Not a synchronisation protocol.
- Not an authority relationship in either direction.

---

## 11. Constraints and prohibitions

Consolidated from `.clinerules/` and the ADRs. Each is checked by `make check` or `make test`.

| # | Constraint | Enforcement |
|---|---|---|
| C1 | No mandatory third-party runtime dependency | `tests/test_dependency_hygiene.py` |
| C2 | No corpus data in version control | `tools/check_repo.py`, `tests/test_repo_hygiene.py` |
| C3 | No microservice, broker, worker pool, or scheduler | Review + `tests/test_dependency_hygiene.py` |
| C4 | No independent graph database | Review + ADR gate |
| C5 | No runtime network I/O | `tests/test_dependency_hygiene.py` |
| C6 | No `pickle`, `eval`, `exec`, `marshal`, or dynamic code generation | `tests/test_dependency_hygiene.py` |
| C7 | No write endpoints on the HTTP surface | `tests/test_api.py` |
| C8 | Loopback-only default binding | `tests/test_api.py` |
| C9 | No autonomous agent execution | Review + absence of implementation |
| C10 | No runtime reference to Gomine | `tests/test_independence.py` |
| C11 | Every claim-bearing record carries a layer | Storage `CHECK` + `tests/test_layers.py` |
| C12 | Ingestion blocked unless licence `verified` | `tests/test_licensing.py` |

---

## 12. Verification

This specification is verified by:

| Check | Command |
|---|---|
| Structure and hygiene | `make check` |
| Module boundaries and dependency direction | `python -m unittest tests.test_module_boundaries` |
| Dependency hygiene | `python -m unittest tests.test_dependency_hygiene` |
| Gomine independence | `python -m unittest tests.test_independence` |
| API read-only and loopback | `python -m unittest tests.test_api` |
| Retrieval degradation | `python -m unittest tests.test_retrieval` |
| Full suite | `make test` |

---

## 13. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.0.0 | M0 | Initial specification. | ADR-0001, ADR-0002, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0009 |
