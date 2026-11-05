# ADR-0007 — Modular knowledge graph in SQLite

| Field | Value |
|---|---|
| **ID** | ADR-0007 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-DATA-001 §6.5; DKF-ARCH-001 §10; src/scriptura/graph/ |
| **Supersedes** | — |

## Context

The brief specifies a **modular knowledge graph**. Two words carry the design:

- **Knowledge graph** — typed nodes and typed edges, not merely foreign keys between tables.
- **Modular** — the graph is composed of separable concerns, each of which can be reasoned about, queried, and
  extended independently.

Per ADR-0005 there is no graph database. Per ADR-0001 the store is SQLite. The question is how to model a graph
relationally without losing graph properties.

A further constraint dominates: **every edge must carry an epistemic layer.** A relationship inferred by a model
must be visibly different from a relationship asserted by a manuscript. A graph that cannot express this is
worse than no graph, because it launders inference into structure.

## Decision

**The knowledge graph is a pair of typed relational tables in SQLite, with layer typing, provenance, and
bounded traversal.**

Specifically:

1. `nodes(id, kind, layer, label, reference_id, payload_json, non_authoritative, source_uri, content_hash,
   actor, created_at)`.
2. `edges(id, source_node_id, target_node_id, relation, layer, non_authoritative, confidence, payload_json,
   source_uri, content_hash, actor, created_at)`.
3. Both tables carry the closed-set `layer` `CHECK` constraint.
4. `edges` carries `CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1)`.
5. Self-edges are prohibited: `CHECK (source_node_id <> target_node_id)`.
6. `relation` is drawn from a registered vocabulary. An unregistered relation is rejected.
7. `kind` is drawn from a registered vocabulary. An unregistered kind is rejected.
8. Traversal is implemented with recursive CTEs, bounded by maximum depth and maximum node count.
9. Every traversal accepts a **layer filter** and reports which layers it traversed.
10. Traversal never silently merges layers.
11. Modularity is achieved through `kind` and `relation` vocabularies plus payload separation, so concerns can be
    added without altering the storage contract.

## Rationale

1. **Layer typing is the point.** A biblical knowledge graph whose edges are all equivalent is actively harmful.
   Enforcing layer at the storage level makes the harmful state unrepresentable.
2. **Relational modelling is sufficient.** Typed nodes and typed edges with indexed adjacency is exactly a
   property graph. Recursive CTEs give bounded traversal.
3. **Constraints over conventions.** `CHECK` constraints cannot be bypassed by a future code path, a script, or
   a direct SQL client.
4. **Modularity without fragmentation.** Vocabulary-based modularity keeps one storage contract while allowing
   many concerns. Separate tables per concern would fragment traversal.
5. **Provenance on edges.** An edge with no source is an assertion, not knowledge.
6. **Bounded traversal.** Unbounded traversal over a graph is a denial-of-service risk and a correctness risk.
   Bounding it is cheap.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **One table per relation type** | Fragments traversal: a query crossing concerns must union many tables. Also multiplies migration surface. |
| **Edge triple table (`subject, predicate, object` as free text)** | Loses referential integrity, loses type safety, and makes layer enforcement awkward. |
| **Adjacency encoded in JSON payloads** | Not queryable, not indexable, not constrainable. |
| **RDF triples in SQLite** | Viable and worth revisiting for **export** to scholarly Linked Data. Rejected as the internal model because it complicates layer enforcement and adds URI-management overhead for no internal benefit. |
| **Graph database** | Rejected by ADR-0005. |
| **Foreign keys only, no explicit edge table** | Cannot carry layer, provenance, or confidence on a relationship. Defeats the purpose. |

## Consequences

### Positive

- Layer, provenance, and confidence are first-class properties of every relationship.
- Inference cannot be laundered into structure.
- One storage contract; modular through vocabularies.
- Traversal is bounded and layer-filterable.
- Constraints enforce what code cannot.

### Negative

- Recursive CTE traversal is slower than a native graph engine for deep traversals. Mitigated: depth is bounded.
- No native graph algorithms. Mitigated: computable in Python over a bounded subgraph.
- Vocabulary registration is a discipline that must be maintained. Mitigated: unregistered values are rejected.

### Neutral

- Payload extension via `payload_json` keeps the contract stable while concerns evolve.

## Compliance

| Document | Effect |
|---|---|
| `docs/architecture/BKB-DATA-001-data-model.md` | §6.5 graph constraints |
| `docs/architecture/DKF-ARCH-001-discovery-framework.md` | §10 relationship to the knowledge graph |
| `.clinerules/020-epistemic-layers.md` | Invariant L10 |
| `src/scriptura/graph/model.py`, `queries.py` | Implementation |

## Verification

| Check | Command |
|---|---|
| Node and edge creation with layer | `python -m unittest tests.test_graph` |
| `ai_hypothesis` edge requires `non_authoritative` | `python -m unittest tests.test_graph` |
| Self-edge rejected | `python -m unittest tests.test_graph` |
| Unregistered kind or relation rejected | `python -m unittest tests.test_graph` |
| Bounded, layer-filtered traversal | `python -m unittest tests.test_graph` |

## Related

ADR-0001, ADR-0005, ADR-0008, BKB-DATA-001, DKF-ARCH-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
