# 020 — Epistemic Layers

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

Scriptura's foundational architectural commitment. This rule is **normative and machine-enforced**.
Superseded in part by [ADR-0011](../docs/architecture/ADR/ADR-0011-seven-layer-epistemic-model.md), which
replaces the original five-layer model with seven layers and removes universal ranking.

---

## 1. Why layers exist

Data in biblical research comes in radically different epistemic kinds. A manuscript reading, an archaeological
date, a morphological parse, a critical monograph, a patristic interpretation, and a machine-generated guess are
not variations on a theme. They have different authorities, different failure modes, and different obligations.

When they are stored undifferentiated, they become indistinguishable at query time — and a model's guess
acquires the rhetorical weight of a manuscript reading simply by sitting in the same result set.

Layers make that collapse **structurally impossible**. Not discouraged: impossible.

## 2. The seven layers

Every persisted record that makes a claim carries exactly one layer. The set is closed at ADR-0011; adding a
layer requires an accepted ADR.

**Layers classify the *nature* of a knowledge record. They are not levels of truth, reliability, or authority.
There is no ranking among them.**

### `scripture`

Text as attested by a **named edition, translation, or manuscript witness**.

- The authority is **the edition**, never "the Bible".
- Every `scripture` record names its edition, its witness where applicable, its language, and its reference.
- **Scripture text is always sourced, never generated.** No agent, model, or process may produce `scripture`
  text. It is copied from an ingested edition, or it does not exist.
- Different editions disagree. That disagreement is recorded, not resolved.
- Canon membership is a property of a **canon profile**, not of a text.

### `textual_observation`

Manuscript readings, textual variants, transmission phenomena, textual criticism, and witness comparisons.

- An apparatus entry records **what witnesses read**, not what the text "should" say.
- A textual observation is a **comparison of witnesses or editions**, and names both sides of it.
- Textual observations are **never** `scripture`: an edition's text and an apparatus note about that text are
  different records.
- Competing readings are preserved side by side. A textual observation never resolves a variant by preference.
- Every observation names its analyst or source dataset.

### `linguistic_observation`

Morphology, syntax, lexicography, semantics, phonology, orthography, and discourse analysis.

- Analytical, not revelatory. A parse is an analysis performed by an analyst or a dataset.
- **Contested readings carry competing analyses.** Where two datasets parse differently, both are stored.
- Every observation names its source dataset or analyst.
- Semantic range claims are observations about attested usage, not definitions imposed on a text.

### `historical_evidence`

Archaeological, documentary, inscriptional, material, and other external historical evidence.

- Evidence stands on its own authority. It does **not** inherit scriptural authority by association.
- Dating is contested and must carry its basis and its uncertainty.
- Evidence for a claim is not the claim. "An inscription mentions X" is evidence; "X happened" is an
  interpretation and belongs elsewhere.

### `scholarly_interpretation`

Academic and critical interpretations attributed to **identifiable scholars, works, and research
publications**.

- **Attribution is mandatory:** a named scholar or author, a named work or publication, and publication
  metadata. An unattributed scholarly interpretation is **rejected at validation**.
- This is the layer for critical monographs, journal articles, and academic commentary.
- It is **never** `theological_interpretation`: academic work and doctrinal positions carry different
  attribution obligations and are verified differently.
- Never presented as fact. "Author X argues in work Y" is a record. "Y is correct" is not.

### `theological_interpretation`

Interpretations attributed to **identifiable theological traditions, authors, works, and doctrinal
frameworks**.

- **Attribution is mandatory.** An interpretation with no named tradition or author is **rejected at
  validation**.
- Never presented as fact. "Augustine reads this as Trinitarian" is a record. "This is Trinitarian" is not.
- Traditions are named precisely. "The church fathers" is not a tradition; a named author with a named work is.
- Modern positions are recorded the same way as ancient ones, with the same attribution requirement.
- It is **never** `scholarly_interpretation`, and vice versa.

### `ai_hypothesis`

Machine-generated suggestions, inferences, patterns, and proposed relationships.

- **Always non-authoritative.** This is definitional, not a policy preference.
- **Must be flagged at every presentation boundary:** API responses, exports, reports, UI, agent output,
  generated documentation.
- May never be promoted by relabelling (see §4).
- Carries the model, the prompt or method, the inputs, and a confidence value.
- Is the **default** layer for anything an agent generates.
- **A high confidence score does not change this.** An AI hypothesis remains an `ai_hypothesis` at every
  confidence value, and citing sources does not change it either.

## 3. No universal ranking

**Removed.** `LAYER_ORDER`, `layer_strength`, `weakest_layer`, and `compose_layer` do not exist. They must not
be reintroduced under another name.

There is **no ordering** of the seven layers by truth, reliability, authority, or warrant. Comparing two layers
for "strength" is a category error: they describe different kinds of claim.

### Independent metadata dimensions

The following dimensions are recorded **independently of layer**. None of them may determine, influence, or
imply a record's epistemic layer:

| # | Dimension |
|---|---|
| 1 | Epistemic layer |
| 2 | Source provenance |
| 3 | Evidence quality |
| 4 | Confidence |
| 5 | Verification status |
| 6 | Scholarly consensus or disagreement, where applicable |
| 7 | Interpretation tradition, where applicable |
| 8 | Author or analyst attribution |

**Rules:**

1. **Confidence and evidence quality never determine layer.** A low-confidence historical claim remains
   `historical_evidence`. A high-confidence AI hypothesis remains `ai_hypothesis`.
2. **Verification status never determines layer.** A verified hypothesis is still a hypothesis; it may be
   *superseded* by a new independently authored record, never relabelled.
3. **Disagreement never determines layer.** A contested reading is still the layer its record belongs to.
4. **A record's layer is chosen from the nature of the claim, never from its perceived strength.**

## 4. Derivation and mixed evidence

Real research draws on several layers at once. The derivation model records that honestly.

### 4.1 Derivation records

A **derivation record** links inputs to outputs and preserves:

- every input record ID **and its original epistemic layer**;
- every output record ID **and its assigned layer**;
- the transformation method and its parameters;
- the human or agent responsible;
- the timestamp, and tool/model identity and version where applicable;
- supporting evidence and source provenance;
- verification status, reviewer, and decision authority;
- disagreements and competing interpretations encountered.

### 4.2 Rules

| # | Rule |
|---|---|
| D1 | **No automatic weakest-layer inheritance.** A derived record's layer is assigned explicitly, never computed from its inputs. |
| D2 | **No automatic promotion to a strongest input's layer.** Strong endpoints do not transfer warrant. |
| D3 | **Multiple outputs are first-class.** One derivation may produce several records of different layers. |
| D4 | **Decompose mixed claims.** A research output containing different kinds of claim is split into appropriately typed records, not stored as one record with a blended layer. |
| D5 | **AI-generated research begins as `ai_hypothesis`.** Always. |
| D6 | **An AI proposal does not become authoritative** because it cites sources or carries a high confidence score. |
| D7 | **Promotion requires a new record.** Moving a claim into another layer requires a new, independently authored and sourced record, an independent verification process, and an auditable human decision where this specification requires it. |
| D8 | **The original hypothesis is never erased.** The full audit history is retained. |
| D9 | **Verified interpretations carry genuine attribution.** Any independently verified `scholarly_interpretation` or `theological_interpretation` must attribute its responsible author, tradition, or publication. Relabelling AI output as a scholarly finding is a Critical integrity incident. |
| D10 | **Disagreements travel with the derivation.** Competing interpretations are preserved, not resolved, not averaged, and not dropped. |

## 5. Invariants

Enforced by `src/scriptura/core/layers.py`, by storage constraints, and by tests.

| # | Invariant | Enforcement |
|---|---|---|
| L1 | Every claim-bearing record has exactly one layer. | Storage `NOT NULL` + `CHECK`; validation |
| L2 | The layer set is closed. Unknown values are rejected. | Enum + storage `CHECK` |
| L3 | `theological_interpretation` requires a non-empty attribution. | Validation rejects |
| L3b | `scholarly_interpretation` requires a named scholar/author **and** a named work. | Validation rejects |
| L3c | `textual_observation` requires a reference, compared witnesses/editions, and an attributed analyst or source dataset. | Validation rejects |
| L4 | `scripture` requires a named edition and a valid reference. | Validation rejects |
| L5 | `ai_hypothesis` requires provenance of generation (model/method + inputs + timestamp). | Validation rejects |
| L6 | `ai_hypothesis` output is flagged at every presentation boundary. | Serialisation enforces |
| L7 | No record may change layer by relabelling. Layer change requires a new record, independent verification, and an auditable human decision. | Validation refuses; audit record required |
| L8 | Layer survives serialisation and deserialisation. | Round-trip tests |
| L9 | Layer survives the Gomine exchange boundary in both directions. | Exchange-format tests |
| L10 | A query may filter by layer; it may never silently merge layers. | Query API requires explicit layer handling |
| L11 | No ranking API exists. Confidence, evidence quality, and verification status never determine layer. | API absence tests |
| L12 | Derivation records preserve every input/output ID and layer. | Derivation validation tests |

## 6. Conditional validation

Per-layer required fields are validated **only for the layer they belong to**. A field inapplicable to the
current layer is never made mandatory for it.

- `scripture`: edition identifier; reference; text; language; normalisation form where relevant; witness where
  applicable; canon profile where relevant.
- `textual_observation`: passage/reference; compared witnesses or editions; readings compared; source of the
  textual evidence; analyst or source dataset; method or observation type.
- `linguistic_observation`: language; reference; form or lemma where applicable; observation type; analysis;
  attributed analyst or source dataset.
- `historical_evidence`: evidence type; source citation; identifier where one exists; dating where applicable;
  dating basis; confidence/uncertainty where appropriate.
- `scholarly_interpretation`: identifiable scholar or author; named work or publication; publication metadata;
  passage or subject where applicable; attributed interpretive argument; supporting references.
- `theological_interpretation`: named tradition or author; named work where applicable; doctrinal or
  interpretive context; passage/reference; attributed interpretive position; source citation.
- `ai_hypothesis`: model identity and version; method or prompt identifier/hash; input record identifiers;
  generated timestamp; confidence if supplied; explicit non-authoritative status.

"Where applicable" and "where relevant" are **conditional** requirements: they are enforced when the data
implies the condition, and ignored when it does not. The validator states which condition triggered a failure.

## 7. Presentation obligations

1. Any output mixing layers must **visibly distinguish** them.
2. Any output containing `ai_hypothesis` must carry a non-removable flag.
3. No output may present a mixed-layer result set in a way that implies uniform authority.
4. Exports must carry layer information. An export format that cannot represent layers may not be used.
5. No output may order or rank records by epistemic layer.

## 8. Common violations

Rejected at review:

- A record persisted with no layer, or with a defaulted layer chosen silently by code.
- `theological_interpretation` stored without attribution.
- `scholarly_interpretation` stored without a named scholar and work.
- A textual variant stored as `scripture`.
- Academic monographs stored as `theological_interpretation` (or the reverse).
- Scripture text produced by a model and stored as `scripture`.
- An AI-derived cross-reference stored as `historical_evidence`.
- A record whose layer was chosen by confidence, evidence quality, or perceived strength.
- A derived record whose layer was computed from its inputs.
- An AI output relabelled as a scholarly or theological finding.
- A query that returns mixed layers with no layer field in the result.
- An export that drops layer information.
- An output that ranks records by layer.
- "The Bible says X" where the record actually says "edition E reads X".

---

**Related:** [010-source-integrity.md](010-source-integrity.md) ·
[030-research-standards.md](030-research-standards.md) ·
[060-agent-safety.md](060-agent-safety.md) ·
[../docs/architecture/BKB-DATA-001-data-model.md](../docs/architecture/BKB-DATA-001-data-model.md) ·
[../docs/architecture/ADR/ADR-0011-seven-layer-epistemic-model.md](../docs/architecture/ADR/ADR-0011-seven-layer-epistemic-model.md) ·
[../docs/architecture/ADR/ADR-0008-epistemic-layer-typing.md](../docs/architecture/ADR/ADR-0008-epistemic-layer-typing.md) (superseded)
