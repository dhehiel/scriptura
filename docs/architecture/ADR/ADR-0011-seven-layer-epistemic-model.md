# ADR-0011 — Seven-Layer Epistemic Model and Removal of Universal Ranking

| Field | Value |
|---|---|
| **ID** | ADR-0011 |
| **Status** | proposed |
| **Date** | M0 (recovery) |
| **Deciders** | *pending human approval* |
| **Affects** | `.clinerules/020`, BKB-DATA-001, BKB-ARCH-001, BKB-CORPUS-001, BKB-AGENTS-001, BKB-VERIFY-001, DKF-ARCH-001, `core/layers.py`, `graph/`, `search/`, `retrieval/`, `api/`, `schemas/core/`, migration `0002` |
| **Supersedes** | ADR-0008 (retained on disk; status `superseded`) |
| **Superseded by** | — |

## Status note

This ADR is **proposed**. Implementation on branch `architecture/seven-layer-epistemic-model` is authorised for
review and approval; it is not approved architecture until a human reviewer records identity and date, and it
is not a milestone gate decision. M0 → M1 remains CLOSED.

## Context

The M0 implementation adopted a five-layer model (`scripture`, `historical_evidence`,
`linguistic_observation`, `theological_interpretation`, `ai_hypothesis`) recorded in ADR-0008, with three
features that the current review shows to be wrong or incomplete:

1. **Universal ranking.** `LAYER_ORDER`, `layer_strength`, `weakest_layer`, and `compose_layer` impose one
   ordering across all layers, and `compose_layer` assigns derived records the *weakest* input layer. This
   conflates the *nature* of a record with its *truth* or *authority*. A low-confidence historical claim remains
   historical evidence; an AI hypothesis remains an AI hypothesis regardless of its confidence score. The
   ordering invites exactly the laundering the layer model exists to prevent, in the opposite direction: a
   "strong" layer absorbs records that never earned it.

2. **Missing textual-criticism layer.** Manuscript readings, variants, and transmission phenomena have nowhere
   to live that is distinct from `scripture` (text *as attested by an edition*) and from
   `linguistic_observation` (analysis of a form). Recording a variant as `scripture` asserts the edition endorses
   a reading the apparatus records as contested; recording it as `linguistic_observation` hides that it is a
   witness comparison rather than an analysis.

3. **Missing scholarly layer.** Academic and critical interpretations attributed to identifiable scholars,
   works, and publications are not the same kind of record as positions attributed to theological traditions and
   doctrinal frameworks. Folding academic work into `theological_interpretation` misclassifies a critical
   monograph as a doctrinal position, and misclassifies a confessional writer as an academic one.

The M0 code also carries one **real, independently reported defect** this ADR fixes: `search/fts.py`'s opening
docstring claims `remove_diacritics 2` "gives accent-insensitive matching over polytonic Greek and pointed
Hebrew" — empirically false on SQLite 3.40.1 (it folds Latin only), contradicting the module's own later
comment and ADR-0009. Two further known defects are fixed in the same programme: layer/edition filters applied
inside the FTS subquery can drop relevant results because the inner `LIMIT` runs before filtering, and
`api/server.py` only *warns* on non-loopback binding rather than rejecting it.

### Constraints

- Preserve the M0 infrastructure: provenance, licensing safeguards, schemas, tests, reference handling, SQLite
  storage, and search. This is a controlled remediation, not a restart.
- Do not silently map existing records to new layers. (At M0 there are no corpus records to remap —
  `corpus_records: 0` — but the rule binds future migrations.)
- Keep real corpus ingestion disabled; the licence gate stays closed.
- Do not rewrite `0001_bootstrap.sql`; migrations are forward-only (BKB-DATA-001 rule M2).

## Decision

### 1. Seven layers, closed set

Exactly these seven epistemic layers exist. Adding one requires a new accepted ADR.

| Value | Definition |
|---|---|
| `scripture` | Text as attested by a named edition, translation, or manuscript witness. Always sourced, never generated. |
| `textual_observation` | Manuscript readings, textual variants, transmission phenomena, textual criticism, witness comparisons. |
| `linguistic_observation` | Morphology, syntax, lexicography, semantics, phonology, orthography, discourse analysis. |
| `historical_evidence` | Archaeological, documentary, inscriptional, material, and other external historical evidence. |
| `scholarly_interpretation` | Academic and critical interpretations attributed to identifiable scholars, works, and research publications. |
| `theological_interpretation` | Interpretations attributed to identifiable theological traditions, authors, works, and doctrinal frameworks. |
| `ai_hypothesis` | Machine-generated suggestions, inferences, patterns, and proposed relationships. Always non-authoritative. |

**No two of these may be combined.** In particular: `textual_observation` is never `scripture`;
`scholarly_interpretation` is never `theological_interpretation`; `ai_hypothesis` is never a human-authored
finding.

### 2. No universal ranking

`LAYER_ORDER`, `layer_strength`, `weakest_layer`, and `compose_layer` are **removed from the API**. The seven
layers classify the *nature* of a knowledge record, not its truth, reliability, or authority. There is no
seven-layer ranking to replace the five-layer one.

Independent metadata dimensions — none of which may determine epistemic layer — are:

- epistemic layer;
- source provenance;
- evidence quality;
- confidence;
- verification status;
- scholarly consensus or disagreement, where applicable;
- interpretation tradition, where applicable;
- author or analyst attribution.

A low-confidence historical claim remains `historical_evidence`. An `ai_hypothesis` remains `ai_hypothesis` at
every confidence score. Confidence and evidence quality never reclassify a record.

### 3. Layer-specific conditional validation (refinement 2)

Each layer has mandatory fields, documented per layer. Conditional requirements are validated explicitly and
**only for the layer they belong to** — a field inapplicable to a given layer is never made mandatory for it.
See §6 for the exact field lists and their SQL enforcement.

### 4. Derivation and evidence chains (refinement 1)

A provenance-preserving derivation model supports **multiple output records** from **multiple inputs**:

- every input record ID **and its original epistemic layer**;
- every output record ID **and its assigned layer**;
- the transformation method and its parameters;
- the human or agent responsible;
- the timestamp, and tool/model identity and version where applicable;
- supporting evidence and source provenance;
- verification status, reviewer, and decision authority;
- disagreements and competing interpretations.

There is **no automatic weakest-layer inheritance** and **no automatic promotion to a strongest input's
layer**. A research output containing different kinds of claim is **decomposed into appropriately typed
records**.

Machine-generated research begins as `ai_hypothesis`. An AI proposal does not become authoritative because it
cites sources or carries a high confidence score. Promoting into another layer requires **a new, independently
authored and sourced record**, an independent verification process, and an auditable human decision where the
specification requires it. **The original hypothesis is never erased**, and the full audit history is retained.

Any independently verified `scholarly_interpretation` or `theological_interpretation` must carry **genuine
attribution** to its responsible author, tradition, or publication. Relabelling an AI output as a scholarly
finding is a Critical integrity incident (SECURITY.md).

### 5. Storage model: wide-table extension (refinement 2)

Layer-specific fields for the two new layers are added as **nullable columns on the existing `claims`, `nodes`,
and `edges` tables** by migration `0002`, rather than as separate extension tables. The trade-off is documented
in full in §7 below.

### 6. Search, retrieval, and API

- FTS `exact` matches against the **stored-form column** without application-level folding; the FTS tokenizer's
  normalization is documented as tokenizer normalization, **not** byte-exactness.
- Byte-exact equality is verified **in application code** comparing the stored string to the candidate string.
- FTS `folded` uses the explicitly folded representation.
- FTS `both` combines both search paths and deduplicates.
- Layer/edition filtering is applied **outside** the FTS subquery, after fetching a bounded candidate set, so
  valid results are not lost to a premature inner `LIMIT`.
- Non-loopback API binding is **rejected by default**. An override flag does not independently authorize public
  exposure: external binding additionally requires explicit security configuration, a documented authentication
  and authorization design, and an explicit operator acknowledgement. Tests pin the loopback-only default.

### 7. Licensing (unchanged gate, tightened rule)

The closed ingestion gate stays. Every **applicable** licence must pass; a dataset remains blocked if **even one**
applicable licence is unresolved or incompatible — including the layered case where a dataset's text and its
annotation carry different licences.

### 8. Ingestion implementation status

The current ingestion implementation performs **preflight validation and preparation**: licence-gate evaluation,
adapter conversion, record validation, and manifest construction. It does **not** yet perform transactional
loading into the corpus tables; `IngestionResult.loaded` is `false` and no adapter may write corpus rows. Real
corpus ingestion remains disabled.

## Rationale

1. **Layers describe kinds of claim, not grades of truth.** Removing the ranking removes the mechanism by which
   a record's *nature* could be confused with its *warrant*, in either direction.
2. **Textual criticism is a real, distinct scholarly practice.** A variant apparatus is not the edition's text
   and not a linguistic analysis; it is a comparison of witnesses, and it must be queryable as such.
3. **Academic work and doctrinal positions fail differently.** A critical monograph can be wrong on its own
   scholarly terms; a doctrinal position can be heterodox relative to its own tradition. Conflating them makes
   both unverifiable.
4. **Conditional validation keeps the model honest.** Fields exist where they are meaningful and are checked
   only there; unrelated fields never become mandatory.
5. **Derivation is where mixed evidence is actually used.** Real research draws on several layers at once; the
   model must record that honestly with full input/output provenance instead of averaging it into one layer.

## Alternatives considered

**Mandatory section.**

| Alternative | Why it was not chosen |
|---|---|
| **Retain five layers** | Leaves textual criticism and academic scholarship without a correct home, forcing misclassification of variants as `scripture` and monographs as `theological_interpretation`. |
| **Seven layers *with* a new seven-step ranking** | Simply repeats the §Context error with more values. A ranking of nature-classes is a category error; it would re-introduce strength-based laundering. |
| **Merge `scholarly_interpretation` into `theological_interpretation`** | Misclassifies critical academic work as doctrinal position, and vice versa; attribution obligations differ (scholar+work+publication vs. tradition+doctrine). |
| **Merge `textual_observation` into `scripture`** | Asserts an edition endorses readings the apparatus records as contested; erases the difference between text and apparatus. |
| **Merge `textual_observation` into `linguistic_observation`** | Hides that it is a witness comparison rather than a formal analysis; witness identity would have nowhere to live. |
| **Add an `evidence_strength` pseudo-layer** | Re-creates ranking under another name; rejected as a category error. |
| **Layer-specific extension tables instead of wide columns** | Correct at larger scale (see §7), but premature now: it multiplies joins on every claim query, complicates the single-file audit story, and would require reworking every existing query and test for no present benefit with `corpus_records: 0`. |
| **Keep `compose_layer` but rename it** | Preserves the prohibited automatic inheritance; any replacement must be explicit derivation records instead. |
| **Silently map five-layer records into seven** | Prohibited by the directive and by honesty rules; there is nothing to map today, and future migrations must preserve identifiers and require review. |

## Consequences

### Positive

- Variants and apparatus are first-class and queryable without asserting edition endorsement.
- Academic and doctrinal interpretation are separately verifiable with the correct attribution obligations.
- No code path can reclassify a record by confidence or evidence quality.
- Derivation records make mixed-evidence research auditable at input and output level.
- Search semantics are stated accurately instead of over-claiming byte-exactness.
- API exposure is fail-closed by default.

### Negative

- Seven layers increase validation and documentation surface.
- Deleting `layer_strength`/`compose_layer` is a breaking API change; contained to in-repo consumers, all
  updated in the same programme.
- Wide-table extension adds nullable columns that only some rows use (see §7).
- Migration `0002` widens `CHECK` constraints; the ledger must be verified after application.
- Non-loopback operators must now pass a security gate instead of a warning.

### Neutral
- No corpus data exists at M0, so no records are reclassified by this migration.
- ADR-0008 is retained as history, marked `superseded`.

## Storage-model trade-off (refinement 2, full discussion)

### Why layer-specific fields are added to existing tables

The two new layers need fields the old model had no column for: compared witnesses and readings for
`textual_observation`; scholar, work, publication metadata, and supporting references for
`scholarly_interpretation`. Migration `0002` adds them as nullable columns on `claims` (and mirrors the
vocabulary on `nodes`/`edges`), because every claim already flows through `claims` and its validators.

### Why wide columns are preferable *at this stage*

1. **One table, one query path.** Every existing reader (`search`, `retrieval`, `api`, `graph`, validation) keeps
   working with minimal change. Extension tables would require LEFT JOINs or unioned queries on every read.
2. **The single-file audit story survives.** The whole store remains one SQLite file with one migration chain.
   Extension tables multiply migration count and join cost for no present benefit.
3. **Scale is currently zero.** `corpus_records: 0`; there are no rows to partition. Optimising a partitioning
   strategy before data exists is speculative design.
4. **Conditional validation is already the pattern.** M0's `claims` table already mixes five layers' fields with
   per-layer `CHECK`s; the design extends an accepted, tested mechanism rather than introducing a second one.

### How conditional validation prevents unrelated fields becoming mandatory

Each layer's `CHECK` constraints and `validate_layer_fields` requirements apply **only when `layer` matches**.
A `scholarly_interpretation` row is never required to carry `evidence_type`; a `historical_evidence` row is never
required to carry `scholar_name`. The validator's per-layer requirement tables are the single source of truth
mirrored by SQL, and a field inapplicable to the current layer is ignored rather than enforced.

### Limitations and migration implications

- **Column bloat.** `claims` grows nullable columns that most rows never use; `SELECT *` widens.
- **Constraint sprawl.** Every new layer adds `CHECK` clauses; the table DDL becomes long and must be read
  carefully.
- **No per-layer index tuning.** Cannot index or `PARTITION BY` layer-specific fields independently without
  extra work.
- **Migration size.** Each future layer widens an already-wide table; repeated widening is the classic failure
  mode of this pattern.

### Conditions to reconsider extension tables

Revisit this design when **any** of the following becomes true, in a new ADR:

1. Row counts make wide-table scans measurably slower than join-based access on representative queries.
2. A third and fourth layer-specific field group arrive, pushing `claims` past a reviewed width budget.
3. Per-layer retention, archival, or access-control policies diverge.
4. Concurrent writers or query workloads require per-layer indexes that wide columns cannot provide.
5. Extension tables can be introduced with a forward-only migration that preserves identifiers, provenance, and
   audit history without a rewrite.

Until then, wide columns plus conditional `CHECK` constraints are the accepted design, with the limitations
above recorded rather than hidden.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/020-epistemic-layers.md` | Seven layers; no ranking; independent dimensions; derivation rules |
| `.clinerules/040-engineering.md` | `layers.py` API contract (no strength API) |
| `docs/architecture/BKB-DATA-001-data-model.md` | §2 rewritten; §2.4 derivation model; SQL for migration 0002 |
| `BKB-ARCH-001` | §8 API security; §10 exchange preserves seven layers |
| `BKB-CORPUS-001` | Multi-licence gate rule; ingestion stages named honestly |
| `BKB-AGENTS-001` | Output layer unchanged (`ai_hypothesis`); mixed inputs via derivation records |
| `BKB-VERIFY-001` | Evidence-chain layers extended; no cross-layer strength ordering |
| `DKF-ARCH-001` | Link-layer rules per endpoint pair; hypothesis links are `ai_hypothesis` |
| `schemas/core/epistemic-layer.schema.json` | Enum → seven values |
| `src/scriptura/storage/migrations/0002_seven_layer_epistemic_model.sql` | Forward-only; widens CHECKs; adds derivation table |
| `NOTICE`, `README.md`, `AGENTS.md` | Layer lists updated |

## Verification

| Check | Command |
|---|---|
| Seven layers + unknown rejection | `python -m unittest tests.test_layers` |
| No ranking API | `python -m unittest tests.test_layers` |
| No automatic promotion | `python -m unittest tests.test_layers` |
| Derivation-chain preservation | `python -m unittest tests.test_derivation` |
| Conditional requirements | `python -m unittest tests.test_layers` |
| Migration 0002 preservation, CHECKs, idempotency | `python -m unittest tests.test_storage` |
| Graph typing + competing edges | `python -m unittest tests.test_graph` |
| Exact/folded FTS + pagination | `python -m unittest tests.test_fts` |
| Non-loopback refusal | `python -m unittest tests.test_api` |
| Multi-licence evaluation | `python -m unittest tests.test_licensing` |
| Ingestion preflight-only + synthetic | `python -m unittest tests.test_ingestion` |
| Gomine round trip, seven layers, derivations | `python -m unittest tests.test_gomine_exchange` |
| Repository hygiene, no corpus | `python -m unittest tests.test_repo_hygiene` |
| Full suite | `make test` |
| Repository checks | `make check` |

## Related records

ADR-0007, ADR-0008 (superseded by this), ADR-0009, ADR-0010; BKB-DATA-001; .clinerules/020, .clinerules/040;
SECURITY.md (integrity incidents).

## Change history

| Date | Change |
|---|---|
| M0 (recovery) | Initial draft, status `proposed`. Supersedes ADR-0008. |
