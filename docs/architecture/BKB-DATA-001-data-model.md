# BKB-DATA-001 — Data Model and Epistemic Layers

**Biblical Knowledge Base — Data Model**

| Field | Value |
|---|---|
| **ID** | BKB-DATA-001 |
| **Status** | Accepted |
| **Version** | 1.1.0 |
| **Milestone** | M0 |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Supersedes** | — |

## Abstract

This specification defines Scriptura's data model: the seven epistemic layers and their invariants, the canonical
reference system, the provenance model, the relational schema over SQLite, identifier policy, Unicode handling,
migration policy, and the serialisation contract. It is the normative source for what may be stored, how it must
be typed, and what must never be collapsed.

---

## 1. Purpose and scope

### 1.1 Purpose

To make it **structurally impossible** to treat a manuscript reading, a piece of external evidence, a linguistic
analysis, a theological interpretation, and a machine-generated hypothesis as interchangeable.

### 1.2 In scope

Epistemic layers; canonical references; provenance; the relational schema; identifiers; Unicode handling;
migrations; serialisation; invariants.

### 1.3 Out of scope

Ingestion lifecycle ([BKB-CORPUS-001](BKB-CORPUS-001-corpus-ingestion.md)); verification semantics
([BKB-VERIFY-001](BKB-VERIFY-001-verification-framework.md)); discovery semantics
([DKF-ARCH-001](DKF-ARCH-001-discovery-framework.md)); agent contracts
([BKB-AGENTS-001](BKB-AGENTS-001-agent-framework.md)).

---

## 2. Epistemic layers

### 2.1 The closed set

Every record that makes a claim carries exactly one epistemic layer. The set is **closed** at ADR-0011.
Adding a layer requires an accepted ADR.

**Layers classify the *nature* of a record, not its truth, reliability, or authority. There is no ranking
among them** (see §2.4).

| Value | Name | Definition | Authority |
|---|---|---|---|
| `scripture` | Scripture | Text as attested by a **named edition, translation, or manuscript witness** | The edition |
| `textual_observation` | Textual observation | Manuscript readings, textual variants, transmission phenomena, textual criticism, witness comparisons | The witnesses compared and the analyst or dataset |
| `linguistic_observation` | Linguistic observation | Morphology, syntax, lexicography, semantics, phonology, orthography, discourse analysis | The analysis and its analyst or dataset |
| `historical_evidence` | Historical evidence | Archaeological, documentary, inscriptional, material, and other external historical evidence | The evidence itself |
| `scholarly_interpretation` | Scholarly interpretation | Academic and critical interpretations attributed to identifiable scholars, works, and research publications | The named scholar, work, and publication |
| `theological_interpretation` | Theological interpretation | Interpretations attributed to identifiable theological traditions, authors, works, and doctrinal frameworks | The named tradition or author |
| `ai_hypothesis` | AI hypothesis | Machine-generated suggestions, inferences, patterns, proposed relationships | **None.** Non-authoritative by definition |

**No two of these may be combined.** `textual_observation` is never `scripture`; `scholarly_interpretation` is
never `theological_interpretation`; `ai_hypothesis` is never a human-authored finding.

### 2.2 Per-layer requirements

#### `scripture`

| Field | Requirement |
|---|---|
| `edition_id` | **Mandatory.** Names the edition. "The Bible" is not an edition. |
| `witness_id` | Mandatory where the edition records witnesses (manuscripts, versions) |
| `reference` | **Mandatory.** A valid canonical reference |
| `text` | **Mandatory.** Copied from the ingested edition. **Never generated.** |
| `language` | **Mandatory.** |
| `normalisation_form` | Mandatory where relevant (original-language text) |
| `canon_profile` | Mandatory where relevant (canon membership) |

Prohibitions: no generated text; no text without an edition; no presentation as "the Bible says" where the
record says "edition E reads".

#### `textual_observation`

| Field | Requirement |
|---|---|
| `reference` | **Mandatory.** The passage under comparison |
| `compared_witnesses` | **Mandatory.** The witnesses or editions being compared (at least two sides) |
| `readings_compared` | **Mandatory.** The actual readings, attributed to their witnesses |
| `source_uri` | **Mandatory.** Source of the textual evidence (apparatus, edition, dataset) |
| `source_dataset` or `analyst` | **Mandatory.** At least one — the observer of the comparison |
| `observation_method` or `observation_type` | **Mandatory.** How the comparison/observation was made |
| `competes_with` | Where competing judgments exist, all are recorded |

Prohibitions: never stored as `scripture` (an apparatus note is not the edition's text); never resolves a
variant by preference; a textual observation never asserts what the text *should* read.

#### `historical_evidence`

| Field | Requirement |
|---|---|
| `evidence_type` | Mandatory: `inscription`, `papyrus`, `ostracon`, `coin`, `archaeological`, `literary`, `documentary`, `other` |
| `identifier` | Mandatory where one exists (catalogue number, siglum, shelf mark) — **copied, never constructed** |
| `dating` | Mandatory, with `dating_basis` and `dating_confidence` |
| `reference` | Optional — the scriptural passage the evidence bears on |
| `source` | **Mandatory.** Resolvable citation |

Prohibitions: evidence does not inherit scriptural authority by association; a date without a basis is rejected.

#### `linguistic_observation`

| Field | Requirement |
|---|---|
| `observation_type` | Mandatory: `morphology`, `syntax`, `lexicon`, `phonology`, `orthography`, `semantics`, `other` |
| `reference` | Mandatory |
| `form` | Mandatory where the observation concerns a form |
| `analysis` | Mandatory |
| `source_dataset` or `analyst` | **Mandatory.** At least one |
| `competes_with` | Where a competing analysis exists, both are recorded |

Prohibitions: no observation without an attributed source; contested readings are never resolved by preference.

#### `theological_interpretation`

| Field | Requirement |
|---|---|
| `tradition` or `author` | **Mandatory.** At least one, non-empty |
| `work` | Mandatory where the author has a named work |
| `reference` | Mandatory |
| `position` | Mandatory — the interpretive claim, as attributed |
| `period` | Recommended |
| `source` | **Mandatory.** Resolvable citation |

Prohibitions: no unattributed interpretation (rejected at validation); never presented as fact; "the church
fathers" is not an attribution — a named author with a named work is.

#### `scholarly_interpretation`

| Field | Requirement |
|---|---|
| `scholar` or `author` | **Mandatory.** An identifiable scholar or author |
| `work` | **Mandatory.** Named work or publication |
| `publication_meta` | **Mandatory.** Publication metadata (venue/year/edition) |
| `reference` or `subject` | Mandatory where applicable |
| `position` | **Mandatory.** The attributed interpretive argument |
| `supporting_refs` | **Mandatory.** Supporting references (the work's own citations) |
| `source_uri` | **Mandatory.** Resolvable citation |

Prohibitions: never stored as `theological_interpretation` (and vice versa); unattributed scholarly
interpretation is rejected at validation; never presented as fact.

#### `ai_hypothesis`

| Field | Requirement |
|---|---|
| `model` | **Mandatory.** Identity and version |
| `method` | **Mandatory.** Prompt or method, or a hash of it |
| `inputs` | **Mandatory.** Input record identifiers |
| `confidence` | **If supplied.** Numeric, in `[0, 1]` — optional, and never a determinant of layer |
| `reference` | Optional |
| `hypothesis` | Mandatory — the inference |
| `generated_at` | **Mandatory.** |
| `non_authoritative` | **Mandatory, always true.** |

Prohibitions: never presented without a flag; never promoted by relabelling; never the sole basis for a
downstream authoritative claim; no generated scripture text. **A high confidence score or the presence of
citations does not make an AI hypothesis authoritative — it remains `ai_hypothesis` at every confidence value.**

### 2.3 Invariants

| # | Invariant | Enforcement |
|---|---|---|
| L1 | Every claim-bearing record has exactly one layer | `NOT NULL` + `CHECK` constraint; validation |
| L2 | The layer set is closed; unknown values rejected | Enum + `CHECK` |
| L3 | `theological_interpretation` requires non-empty attribution | Validation |
| L3b | `scholarly_interpretation` requires a named scholar/author **and** a named work | Validation + `CHECK` |
| L3c | `textual_observation` requires reference, compared witnesses, and an attributed analyst/dataset | Validation + `CHECK` |
| L4 | `scripture` requires edition and valid reference | Validation |
| L5 | `ai_hypothesis` requires generation provenance | Validation |
| L6 | `ai_hypothesis` output is flagged at every presentation boundary | Serialisation |
| L7 | No record changes layer by relabelling. Layer change requires a new independently authored and sourced record, independent verification, and an auditable human decision | Validation refuses; audit record required |
| L8 | Layer survives serialisation round-trip | Tests |
| L9 | Layer survives the Gomine boundary both ways | Exchange tests |
| L10 | A query may filter by layer; may never silently merge layers | Query API |
| L11 | No ranking API exists; confidence, evidence quality, and verification status never determine layer | API-absence tests |
| L12 | Derivation records preserve every input/output record ID and its layer | Derivation validation tests |

### 2.4 No universal ranking

**There is no ordering of the seven layers.** The universal ranking previously specified here
(`LAYER_ORDER`, `layer_strength`, `weakest_layer`, `compose_layer`) is **removed** by ADR-0011. Comparing two
layers for "strength" is a category error: they describe different kinds of claim, not grades of truth.

The following dimensions are recorded **independently of layer**. None may determine, influence, or imply a
record's epistemic layer:

| # | Dimension |
|---|---|
| 1 | Epistemic layer |
| 2 | Source provenance |
| 3 | Evidence quality |
| 4 | Confidence |
| 5 | Verification status |
| 6 | Scholarly consensus or disagreement, where applicable |
| 7 | Interpretive tradition, where applicable |
| 8 | Author or analyst attribution |

**Rules:**

1. **Confidence and evidence quality never determine layer.** A low-confidence historical claim remains
   `historical_evidence`; an AI hypothesis remains `ai_hypothesis` at any confidence score.
2. **Verification status never determines layer.** A verified hypothesis may be *superseded* by a new
   independently authored record; it is never relabelled.
3. **No output may rank records by epistemic layer** (rule X9).
4. **`scripture` is never a layer target for generated content**, under any circumstances.

### 2.5 Derivation and mixed evidence

Real research draws on several layers at once. A **derivation record** links inputs to outputs and preserves
all of:

- every input record ID **and its original epistemic layer**;
- every output record ID **and its assigned layer**;
- the transformation method and its parameters;
- the human or agent responsible;
- the timestamp, and tool/model identity and version where applicable;
- supporting evidence and source provenance;
- verification status, reviewer, and decision authority;
- disagreements and competing interpretations encountered.

**Rules:**

| # | Rule |
|---|---|
| D1 | **No automatic weakest-layer inheritance.** A derived record's layer is assigned explicitly, never computed from its inputs. |
| D2 | **No automatic promotion to a strongest input's layer.** Strong endpoints do not transfer warrant. |
| D3 | **Multiple outputs are first-class.** One derivation may produce several records of different layers. |
| D4 | **Decompose mixed claims.** An output containing different kinds of claim is split into appropriately typed records, never stored as one record with a blended layer. |
| D5 | **AI-generated research begins as `ai_hypothesis`.** |
| D6 | **An AI proposal does not become authoritative** because it cites sources or carries high confidence. |
| D7 | **Layer change requires a new, independently authored and sourced record**, independent verification, and an auditable human decision where required. |
| D8 | **The original hypothesis is never erased.** The full audit history is retained. |
| D9 | **Verified scholarly or theological interpretations carry genuine attribution** to the responsible author, tradition, or publication. Relabelling AI output as a scholarly finding is a Critical integrity incident. |
| D10 | **Disagreements travel with the derivation** — preserved, not averaged, not dropped. |

---

## 3. Canonical references

### 3.1 Purpose

A reference must be unambiguous, stable, comparable, and independent of any single edition's numbering. Different
editions divide chapters and verses differently; the reference system must represent that without loss.

### 3.2 Reference form

A canonical reference is:

```
<book>[ <chapter>[ : <verse>[ .. <verse> ] ] ]
```

Structured as:

| Component | Type | Notes |
|---|---|---|
| `book` | string | Key from the book registry, not a display name |
| `chapter` | int \| null | Null for single-chapter books |
| `verse_start` | int \| null | Null for a chapter-level reference |
| `verse_end` | int \| null | Null or equal to `verse_start` for a single verse |
| `canon_profile` | string | Which canon the book key belongs to |

### 3.3 Book registry

Books are identified by **stable keys**, never by display names, which vary by language and tradition.

Each book record carries:

| Field | Purpose |
|---|---|
| `key` | Stable identifier, e.g. `Gen`, `1Kgs`, `Matt` |
| `names` | Display names by language |
| `aliases` | Accepted alternative abbreviations |
| `chapters` | Chapter count for validation |
| `canon_profiles` | Which profiles include this book |
| `order` | Position within each profile |

### 3.4 Canon profiles

Canon membership is a property of a **profile**, not of a text. The same book may be `scripture` in one profile
and not in another. Scriptura records profiles; it endorses none.

| Profile | Scope |
|---|---|
| `protestant_66` | 39 OT + 27 NT |
| `catholic_73` | Includes the deuterocanonical books |
| `orthodox_broad` | Includes the wider Orthodox canon |
| `hebrew_bible_24` | Tanakh arrangement |
| `nt_27` | New Testament only |
| `deuterocanonical` | Deuterocanonical books only |

**Rules:**

1. A profile is an ordered list of book keys. It does not assert canonicity; it records an arrangement.
2. Adding a profile is an extension at a defined seam. It must not alter an existing profile.
3. A reference must be validated **against a profile**. A book absent from the profile is invalid in it.
4. Chapter and verse counts are validated against the book registry, and edition-specific divergence is
   recorded rather than forced into a single numbering.

### 3.5 Reference invariants

| # | Invariant |
|---|---|
| R1 | A reference is immutable once minted |
| R2 | `verse_end >= verse_start` where both present |
| R3 | Chapter and verse numbers are positive integers |
| R4 | A book key must exist in the registry |
| R5 | A reference is valid only relative to a named profile |
| R6 | References are comparable within a profile via a total order |
| R7 | Display strings are derived from a reference, never parsed from an untrusted display string without validation |
| R8 | Edition-specific numbering divergence is recorded as a mapping, not silently reconciled |

### 3.6 Parsing

Parsing accepts common forms and normalises to the structured representation:

- `John 3:16`, `Jn 3:16`, `JHN 3:16`, `John 3:16-18`, `John 3:16,18`
- `1 Kings 2:4`, `1Ki 2:4`
- `Philemon 2`, `Phm 2`

Parsing is **strict**: an unresolvable book key, an out-of-range chapter, or an inverted range raises rather
than returning a best guess. Guessing a reference is a source-integrity violation.

---

## 4. Provenance model

### 4.1 Principle

> **No orphan records.** Every persisted record carries provenance.

### 4.2 Provenance fields

| Field | Requirement |
|---|---|
| `source_uri` | Resolvable locator: URL, DOI, edition+reference, or dataset+record identifier |
| `source_kind` | `primary`, `secondary`, `derived`, `generated` |
| `retrieved_at` | When the source was consulted |
| `content_hash` | Cryptographic digest of the content as retrieved |
| `dataset_id` | Where the record came from an ingested dataset |
| `licence_id` | The licence record governing the source |
| `actor` | Who or what created the record |
| `created_at` | When |
| `supersedes` | Where this record supersedes an earlier one |

### 4.3 Append-only

Provenance records are **append-only**. They are never silently mutated or deleted.

Correction is by appending a superseding record naming what was wrong, what is correct, the evidence, the date,
and the actor. Silent deletion or mutation is a Critical integrity incident.

### 4.4 Content hashing

- Algorithm: SHA-256 over the canonical byte representation.
- Canonicalisation: UTF-8, with the Unicode normalisation form recorded.
- A record whose content does not hash to its recorded digest is a data-integrity incident.
- Hashes are recorded for retrieved artefacts and for derived artefacts.

### 4.5 Derived records

A derived record records its derivation: the input identifiers, the transformation, and the code version. A
derivation that cannot be reproduced is a claim, not a finding.

---

## 5. Identifier policy

| # | Rule |
|---|---|
| ID1 | Scriptura mints **its own** stable identifiers for every entity |
| ID2 | External identifiers are stored as **mappings**, never adopted as primary keys |
| ID3 | Identifiers are opaque. No semantics are encoded in them |
| ID4 | Identifiers are never reused, even after deletion |
| ID5 | Identifier collisions across datasets are prevented by namespacing |
| ID6 | An identifier collision is a High-severity integrity incident |
| ID7 | Mappings are many-to-many and carry provenance |

Identifier form: `<namespace>:<type>:<opaque>`, for example `scriptura:verse:a1b2c3d4`. The opaque component is
derived from a content-addressable digest, making identifiers reproducible across independent ingestions of the
same source.

---

## 6. Relational schema

### 6.1 Design rules

| # | Rule |
|---|---|
| S1 | Layer invariants are enforced by `CHECK` constraints, not only by application code |
| S1b | Edges additionally carry `verification_status` and supporting evidence (see §6.5) |
| S2 | Foreign keys are enforced on every connection (`PRAGMA foreign_keys = ON`) |
| S3 | Provenance columns are `NOT NULL` where applicable — orphan records cannot be inserted |
| S4 | Every claim-bearing table carries `layer`, `source_uri`, `content_hash`, `actor`, `created_at` |
| S5 | Timestamps are ISO 8601 UTC strings |
| S6 | No implicit defaults for `layer`, `source_uri`, or `actor` |
| S7 | Deletions of provenance-bearing rows are prohibited by policy; enforcement is by review and by the absence of any delete path in the API |

### 6.2 Table inventory

| Table | Purpose |
|---|---|
| `schema_migrations` | Forward-only migration ledger |
| `licences` | Licence records; drive the ingestion gate |
| `datasets` | Ingested datasets with provenance and licence linkage |
| `canon_profiles` | Canon arrangements |
| `books` | Book registry |
| `book_canon_membership` | Book ↔ profile membership and order |
| `canonical_references` | Immutable canonical references. Named so because `REFERENCES` is a reserved word in SQL |
| `editions` | Named editions |
| `witnesses` | Manuscripts and versions |
| `corpus_records` | `scripture`-layer text records |
| `claims` | Claim-bearing records across all seven layers (see §6.3) |
| `nodes` | Knowledge graph nodes |
| `edges` | Knowledge graph edges |
| `identifier_mappings` | Scriptura identifier ↔ external identifier |
| `provenance_events` | Append-only provenance and promotion audit |
| `derivations` | Derivation records linking inputs to outputs with method, actor, and audit fields |
| `ingestion_runs` | Ingestion audit |
| `corpus_fts` | FTS5 index over corpus text |
| `claim_fts` | FTS5 index over claim statements |

### 6.3 Layer enforcement in SQL

The closed layer set is enforced at the storage level:

```sql
layer TEXT NOT NULL CHECK (layer IN (
  'scripture',
  'textual_observation',
  'linguistic_observation',
  'historical_evidence',
  'scholarly_interpretation',
  'theological_interpretation',
  'ai_hypothesis'
))
```

Enforced by migration `0002_seven_layer_epistemic_model.sql`, which widens the M0 five-value `CHECK`s on
`claims`, `nodes`, and `edges` and adds the layer-specific nullable columns described below. Migration 0001 is
never edited (rule M2).

Per-layer requirements are enforced by `CHECK` constraints on `claims`:

```sql
-- L3: theological_interpretation requires attribution
CHECK (layer <> 'theological_interpretation'
       OR (COALESCE(tradition,'') <> '' OR COALESCE(author,'') <> ''))

-- L4: scripture requires an edition and a reference
CHECK (layer <> 'scripture'
       OR (edition_id IS NOT NULL AND reference_id IS NOT NULL))

-- L5: ai_hypothesis requires generation provenance.
-- confidence is IF SUPPLIED (ADR-0011): optional, and never a determinant of layer.
CHECK (layer <> 'ai_hypothesis'
       OR (model IS NOT NULL AND method IS NOT NULL
           AND inputs_json IS NOT NULL
           AND generated_at IS NOT NULL))

-- L6: ai_hypothesis is always flagged non-authoritative
CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1)

-- linguistic_observation requires an attributed source
CHECK (layer <> 'linguistic_observation'
       OR (COALESCE(source_dataset,'') <> '' OR COALESCE(analyst,'') <> ''))

-- historical_evidence requires a type
CHECK (layer <> 'historical_evidence' OR evidence_type IS NOT NULL)

-- L3b: scholarly_interpretation requires a named scholar/author AND a named work.
-- Parentheses matter: without them OR/AND precedence would make `work` mandatory
-- for EVERY layer, not only scholarly_interpretation.
CHECK (layer <> 'scholarly_interpretation'
       OR ((COALESCE(scholar,'') <> '' OR COALESCE(author,'') <> '')
           AND COALESCE(work,'') <> ''))

-- L3c: textual_observation requires a reference, compared witnesses,
-- readings, and an attributed analyst or source dataset
CHECK (layer <> 'textual_observation'
       OR (reference_id IS NOT NULL
           AND COALESCE(compared_witnesses,'') <> ''
           AND COALESCE(readings_compared,'') <> ''
           AND (COALESCE(source_dataset,'') <> '' OR COALESCE(analyst,'') <> '')))

-- confidence, where present, is a probability. It NEVER determines layer (L11).
CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0))
```

**Conditional validation:** every `layer <> '...'` guard means a field is required *only* for its own layer.
A `historical_evidence` row is never required to carry `scholar_name`; a `scholarly_interpretation` row is never
required to carry `evidence_type`. Fields inapplicable to the current layer are ignored, not enforced.

**Derivation table** (added by migration 0002; see §2.5):

```sql
CREATE TABLE derivations (
  id                 TEXT PRIMARY KEY,
  output_ids         TEXT NOT NULL,  -- JSON array of output record IDs
  output_layers      TEXT NOT NULL,  -- JSON array, aligned with output_ids
  input_ids          TEXT NOT NULL,  -- JSON array of input record IDs
  input_layers       TEXT NOT NULL,  -- JSON array, aligned with input_ids
  method             TEXT NOT NULL,
  parameters_json    TEXT,
  actor              TEXT NOT NULL,
  tool_identity      TEXT,
  tool_version       TEXT,
  created_at         TEXT NOT NULL,
  verification_state TEXT,
  reviewer           TEXT,
  decision_authority TEXT,
  evidence_json      TEXT,           -- supporting evidence and source provenance
  disagreements_json TEXT            -- competing interpretations preserved
);
```

An output record's layer is recorded on the output record itself **and** mirrored in `output_layers`; it is
assigned explicitly and never computed from `input_layers` (rules D1–D2).

This means an unattributed interpretation, a generated scripture record without an edition, or an unflagged AI
hypothesis **cannot be inserted**. The database refuses. This is deliberate: a constraint that lives only in
application code can be bypassed by a future code path, a script, or a direct SQL client.

### 6.4 Reference constraints

```sql
CREATE TABLE canonical_references (
  id                TEXT PRIMARY KEY,
  book_id           TEXT NOT NULL REFERENCES books(id),
  canon_profile_id  TEXT NOT NULL REFERENCES canon_profiles(id),
  chapter           INTEGER,
  verse_start       INTEGER,
  verse_end         INTEGER,
  display           TEXT NOT NULL,
  UNIQUE (book_id, canon_profile_id, chapter, verse_start, verse_end),
  CHECK (chapter IS NULL OR chapter > 0),
  CHECK (verse_start IS NULL OR verse_start > 0),
  CHECK (verse_end IS NULL OR verse_start IS NOT NULL),
  CHECK (verse_end IS NULL OR verse_end >= verse_start)
);
```

### 6.5 Graph constraints

```sql
CREATE TABLE edges (
  id                  TEXT PRIMARY KEY,
  source_node_id      TEXT NOT NULL REFERENCES nodes(id),
  target_node_id      TEXT NOT NULL REFERENCES nodes(id),
  relation            TEXT NOT NULL,
  layer               TEXT NOT NULL CHECK (layer IN (...)),   -- seven values (0002)
  non_authoritative   INTEGER NOT NULL DEFAULT 0,
  confidence          REAL,
  verification_status TEXT,             -- independent dimension (§2.4)
  supporting_evidence TEXT,             -- evidence backing this relationship
  payload_json        TEXT,
  source_uri          TEXT NOT NULL,
  content_hash        TEXT NOT NULL,
  actor               TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  CHECK (source_node_id <> target_node_id),
  CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),
  CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0))
);
```

Self-edges are prohibited at M0. A relation requiring one needs an ADR.

**Every relationship retains:** relation type; source and target identifiers; provenance (`source_uri`,
`content_hash`, `actor`, `created_at`); the author or proposing agent (`actor`); supporting evidence
(`supporting_evidence`); verification status (`verification_status`); and its epistemic layer.

**Competing relationships are preserved.** Where two sources assert different relations between the same
endpoints, both edges exist. Edges are never deduplicated by endpoint pair, and a disagreement is never
resolved by keeping one side.

Typical typed relations (registered in `graph/model.py`): a witness `attests` a reading; a textual observation
`compares` readings; a linguistic observation `analyses` a form; a scholarly interpretation `argues_for` an
explanation; a theological interpretation `interprets` a passage; an AI hypothesis `proposes` a possible
relationship. No agent writes directly into authoritative graph records without the validation and verification
process: an agent's proposed edge is `ai_hypothesis` and `non_authoritative = 1` unless an authorised derivation
record with independent verification exists.

### 6.6 Append-only audit

```sql
CREATE TABLE provenance_events (
  id            TEXT PRIMARY KEY,
  entity_kind   TEXT NOT NULL,
  entity_id     TEXT NOT NULL,
  event_type    TEXT NOT NULL CHECK (event_type IN (
                  'created','superseded','promoted','demoted','corrected','flagged')),
  from_layer    TEXT,
  to_layer      TEXT,
  evidence      TEXT,
  reasoning     TEXT,
  actor         TEXT NOT NULL,
  occurred_at   TEXT NOT NULL,
  CHECK (event_type NOT IN ('promoted','demoted')
         OR (from_layer IS NOT NULL AND to_layer IS NOT NULL
             AND actor IS NOT NULL AND reasoning IS NOT NULL))
);
```

A layer promotion without evidence, reasoning, and actor **cannot be inserted**.

---

## 7. Unicode and text handling

| # | Rule |
|---|---|
| U1 | All text is stored as UTF-8 |
| U2 | The Unicode normalisation form is recorded for original-language text |
| U3 | Text is **never silently normalised.** Normalisation is an explicit, recorded transformation |
| U4 | Combining marks, directionality, and cantillation are preserved |
| U5 | No silent transliteration |
| U6 | FTS5 indexing may fold diacritics for **matching**, but the stored text is never altered. FTS5's own `remove_diacritics` folds Latin only; Greek and Hebrew folding is explicit, via `scriptura.core.text.fold_diacritics`, into a separate indexed column |
| U7 | Byte-exact comparison uses the stored text; match comparison may use a folded form |

Rule U6 is important: diacritic folding is a **search** affordance. Greek polytonic and Hebrew pointing must be
searchable without diacritics, but the underlying text must remain exactly as the edition attests it.
The folding is explicit, not delegated to FTS5's built-in option: verified on SQLite 3.40.1 that FTS5
`remove_diacritics 2` folds Latin diacritics only and does not fold Greek polytonic or Hebrew niqqud.
Matching is a union over the original and folded columns, never transliteration. Greek final sigma is
normalised symmetrically in the folded column; the stored text is untouched.

---

## 8. Migration policy

| # | Rule |
|---|---|
| M1 | Migrations are **additive and forward-only** |
| M2 | An applied migration is never edited |
| M3 | Migrations are numbered sequentially and named `NNNN_description.sql` |
| M4 | Each migration runs inside a transaction |
| M5 | The ledger records sequence, name, applied timestamp, and the SHA-256 of the file |
| M6 | Applying an already-applied migration is a no-op, not an error |
| M7 | A ledger hash mismatch is a Critical integrity incident — it indicates an edited migration |
| M8 | Down-migrations are not supported. Reversal is by a new forward migration |
| M9 | Destructive migrations require an ADR and maintainer approval |
| M10 | Migration `0002_seven_layer_epistemic_model` widens the layer `CHECK`s, adds nullable layer-specific columns and the `derivations` table. It is additive, preserves all identifiers and rows, and is verified for idempotency before application to any shared database |

---

## 9. Serialisation contract

### 9.1 Rules

| # | Rule |
|---|---|
| X1 | Serialisation format is JSON, via stdlib `json` |
| X2 | Layer is **mandatory** in every serialised claim-bearing record |
| X3 | Provenance is preserved or explicitly marked absent |
| X4 | Licence reference is preserved for dataset-derived records |
| X5 | `ai_hypothesis` records serialise with `non_authoritative: true` — the field is never omitted |
| X6 | Round-trip must be lossless for layer, provenance, and reference |
| X7 | An export format that cannot represent layers may not be used |
| X8 | No `pickle`, no `marshal`, no dynamic code generation |
| X9 | No output may rank or order records by epistemic layer |
| X10 | Serialised derivations preserve every input/output record ID with its layer, method, actor, and timestamps |

### 9.2 Canonical record shape

```json
{
  "id": "scriptura:claim:...",
  "layer": "linguistic_observation",
  "non_authoritative": false,
  "statement": "...",
  "reference": {"book": "Jhn", "chapter": 1, "verse_start": 18, "verse_end": 18,
                "canon_profile": "protestant_66"},
  "layer_fields": {"observation_type": "morphology", "analysis": "...", "source_dataset": "..."},
  "provenance": {
    "source_uri": "...", "source_kind": "primary", "retrieved_at": "...",
    "content_hash": "sha256:...", "actor": "...", "created_at": "..."
  },
  "licence_id": "...",
  "confidence": null
}
```

`layer`, `provenance`, and `non_authoritative` are always present. A consumer that drops them is a defective
consumer.

---

## 10. Invariants summary

| Class | Invariants |
|---|---|
| Layers | L1–L12 (§2.3) |
| Derivation | D1–D10 (§2.5) |
| No ranking | §2.4; rule X9 |
| References | R1–R8 (§3.5) |
| Identifiers | ID1–ID7 (§5) |
| Schema | S1–S7 (§6.1) |
| Unicode | U1–U7 (§7) |
| Migrations | M1–M9 (§8) |
| Serialisation | X1–X8 (§9.1) |

An implementation that violates any invariant is defective regardless of whether it passes its tests.

---

## 11. Verification

| Check | Command |
|---|---|
| Layer enum, closed set, flagging | `python -m unittest tests.test_layers` |
| Per-layer validation, including rejection | `python -m unittest tests.test_layers` |
| Reference parsing, ranges, profiles, strictness | `python -m unittest tests.test_reference` |
| Schema creation and constraints | `python -m unittest tests.test_storage` |
| Migration ledger and hash mismatch detection | `python -m unittest tests.test_storage` |
| Graph constraints | `python -m unittest tests.test_graph` |
| Serialisation round-trip and layer preservation | `python -m unittest tests.test_serialisation` |
| Schema conformance of registry files | `python -m unittest tests.test_schemas` |
| Seven layers + unknown rejection + no ranking API | `python -m unittest tests.test_layers` |
| Derivation-chain preservation | `python -m unittest tests.test_derivation` |
| Migration 0002 preservation, CHECKs, idempotency | `python -m unittest tests.test_storage` |
| Gomine exchange round trip (seven layers, derivations) | `python -m unittest tests.test_gomine_exchange` |
| Full suite | `make test` |

---

## 12. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.1.0 | M0 (recovery R5) | Seven-layer model; universal ranking removed (§2.4); derivation model (§2.5); `textual_observation` and `scholarly_interpretation` fields + CHECKs; `derivations` table; edge verification/evidence; rules X9–X10. Migration `0002`. | ADR-0011 |
| 1.0.1 | M0 (recovery) | U6 clarified: explicit folded column; built-in `remove_diacritics` verified Latin-only. | ADR-0009 |
| 1.0.0 | M0 | Initial specification: five layers, reference system, provenance model, relational schema, identifier policy, Unicode rules, migration policy, serialisation contract. | ADR-0007, ADR-0008 |
