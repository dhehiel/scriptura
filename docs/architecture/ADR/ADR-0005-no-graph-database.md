# ADR-0005 — No independent graph database

| Field | Value |
|---|---|
| **ID** | ADR-0005 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §5.3; BKB-DATA-001 §6; DKF-ARCH-001 §10 |
| **Supersedes** | — |

## Context

Scriptura's central data structure is a knowledge graph: typed nodes (passages, editions, witnesses, terms,
persons, places, evidence items, interpretations, hypotheses) connected by typed, layer-bearing, provenance-
bearing edges.

It is therefore natural to ask whether a graph database is warranted. The brief explicitly prohibits introducing
one without an approved architecture decision, which is the correct default: a graph database is a second
persistent store, a second query language, a second consistency model, and a server process.

The question is whether the traversal requirements exceed what indexed relational tables can deliver.

Observed requirements at M0 and foreseeable through M3:

- Bounded graph size (the biblical corpus and its related literature are finite).
- Traversal depth in the low single digits for almost all queries.
- Layer-filtered traversal — every query must be able to restrict by epistemic layer.
- Provenance on every edge.
- Full auditability of the store as a single artefact.

## Decision

**No independent graph database is introduced.** The knowledge graph is implemented as typed relational tables
in the same SQLite file that holds everything else. See ADR-0007.

Specifically:

1. Nodes and edges are SQLite tables with foreign keys to each other.
2. Traversal is implemented as recursive CTEs and indexed joins.
3. Every edge carries `layer`, provenance, and an optional confidence.
4. Traversal queries support layer filtering as a first-class parameter.
5. Introducing Neo4j, JanusGraph, TigerGraph, ArangoDB, Memgraph, TerminusDB, or any equivalent requires an
   accepted ADR that **first demonstrates** that the SQLite graph model cannot satisfy the requirement.
6. That demonstration must include the specific query, its measured performance on realistic data, and an
   explanation of why an index or a query rewrite does not resolve it.

## Rationale

1. **One store, not two.** A second persistent store introduces a consistency problem between stores, a second
   migration path, a second backup story, and a second failure mode. For a research instrument, that complexity
   buys nothing.
2. **Auditability.** ADR-0001's central benefit — the whole store is one hashable file — is destroyed by a graph
   database.
3. **Layer invariants.** The epistemic layer must be enforceable by `CHECK` constraints. A graph database's
   schema facilities would need to be re-verified to provide equivalent enforcement.
4. **Scale fit.** The graph is bounded. Recursive CTEs over indexed tables handle low-depth traversal over
   millions of edges comfortably.
5. **No server.** A graph database is a server process: credentials, a listening socket, an authentication
   surface, operational burden.
6. **The prohibition is the right default.** Requiring a demonstration of insufficiency before adoption prevents
   adoption by fashion.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **Neo4j** | Server process, second store, Cypher as a second query language, and the single-file auditability of ADR-0001 is lost. No demonstrated requirement. |
| **RDF triple store (Blazegraph, GraphDB, Jena)** | Attractive for interoperability with scholarly Linked Data, and genuinely worth revisiting for the **exchange boundary** with external ontologies. Rejected as the primary store for the same reasons as Neo4j. An ADR covering RDF *export* is a separate and reasonable future proposal. |
| **Property graph in PostgreSQL (AGE)** | Still a server, and ADR-0001 already rejected PostgreSQL. |
| **In-memory graph library (NetworkX)** | Not persistent, not auditable, and would duplicate the store in memory. |
| **SQLite with a graph extension** | Adds a native extension dependency and platform-specific build requirements, contrary to ADR-0002. |

## Consequences

### Positive

- One store, one query language, one migration path, one backup story.
- Single-file auditability preserved.
- Layer invariants enforced by `CHECK` constraints.
- No server, no credentials, no listening socket.

### Negative

- Deep unbounded traversals are slower than in a native graph engine. Mitigated: traversal depth and node count
  are bounded by specification (DKF-ARCH-001 §10, KG5).
- No native graph query language. Mitigated: recursive CTEs are expressive enough for the required patterns and
  are wrapped in a small query API so callers do not write raw SQL.
- No native graph algorithms (PageRank, community detection). Accepted at M0; if required, they can be computed
  in Python over a bounded subgraph, or revisited by ADR.

### Neutral

- RDF/Linked Data export remains a viable future interoperability path and is not foreclosed by this decision.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/000-project-governance.md` | §3 standing constraint 4 |
| `.clinerules/040-engineering.md` | §1 baseline table |
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §5.3 prohibition; §11 constraint C4 |
| `docs/architecture/BKB-DATA-001-data-model.md` | §6.5 graph constraints |
| `docs/architecture/DKF-ARCH-001-discovery-framework.md` | §10 rule KG6 |

## Verification

| Check | Command |
|---|---|
| Graph operations work on SQLite | `python -m unittest tests.test_graph` |
| Layer-filtered traversal | `python -m unittest tests.test_graph` |
| No graph database dependency | `python -m unittest tests.test_dependency_hygiene` |
| Recursive traversal bounded | `python -m unittest tests.test_graph` |

## Related

ADR-0001, ADR-0007, ADR-0008, BKB-ARCH-001, BKB-DATA-001, DKF-ARCH-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
