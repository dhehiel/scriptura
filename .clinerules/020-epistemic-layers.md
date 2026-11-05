# 020 — Epistemic Layers

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

Scriptura's foundational architectural commitment. This rule is **normative and machine-enforced**.

---

## 1. Why layers exist

Data in biblical research comes in radically different epistemic kinds. A manuscript reading, an archaeological
date, a morphological parse, a patristic interpretation, and a machine-generated guess are not variations on a
theme. They have different authorities, different failure modes, and different obligations.

When they are stored undifferentiated, they become indistinguishable at query time — and then a model's guess
acquires the rhetorical weight of a manuscript reading simply by sitting in the same result set.

Layers make that collapse **structurally impossible**. Not discouraged: impossible.

## 2. The five layers

Every persisted record that makes a claim carries exactly one layer. The set is closed at M0; adding a layer
requires an accepted ADR.

### `scripture`

Text of a witness, **as attested by a named edition**.

- The authority is **the edition**, never "the Bible".
- Every `scripture` record names its edition, its witness where applicable, and its reference.
- **Scripture text is always sourced, never generated.** No agent, model, or process may produce `scripture`
  text. It is copied from an ingested edition, or it does not exist.
- Different editions disagree. That disagreement is recorded, not resolved.
- Canon membership is a property of a **canon profile**, not of a text. The same book may be `scripture` in one
  profile and not in another. Scriptura records profiles; it does not endorse one.

### `historical_evidence`

Material and documentary evidence **external to scripture**.

- Inscriptions, ostraca, papyri, coins, archaeology, ancient historians, contemporaneous documents.
- Evidence stands on its own authority. It does **not** inherit scriptural authority by association.
- Dating is contested and must carry its basis and its uncertainty.
- Evidence for a claim is not the claim. "An inscription mentions X" is evidence; "X happened" is an
  interpretation and belongs elsewhere.

### `linguistic_observation`

Morphology, syntax, lexicography, philology.

- Analytical, not revelatory. A parse is an analysis performed by an analyst or a dataset.
- **Contested readings carry competing analyses.** Where two datasets parse differently, both are stored.
- Every observation names its source dataset or analyst.
- Semantic range claims are observations about attested usage, not definitions imposed on a text.

### `theological_interpretation`

Interpretive positions of **named traditions and authors**.

- **Attribution is mandatory.** An interpretation with no named tradition or author is **rejected at
  validation**.
- Never presented as fact. "Augustine reads this as Trinitarian" is a record. "This is Trinitarian" is not.
- Traditions are named precisely. "The church fathers" is not a tradition; a named author with a named work is.
- Modern positions are recorded the same way as ancient ones, with the same attribution requirement.

### `ai_hypothesis`

Machine-generated inference.

- **Always non-authoritative.** This is definitional, not a policy preference.
- **Must be flagged at every presentation boundary:** API responses, exports, reports, UI, agent output,
  generated documentation.
- May never be promoted by relabelling. See §4.
- Carries the model, the prompt or method, the inputs, and a confidence value.
- Is the **default** layer for anything an agent generates.

## 3. Invariants

These are enforced by `src/scriptura/core/layers.py`, by storage constraints, and by tests.

| # | Invariant | Enforcement |
|---|---|---|
| L1 | Every claim-bearing record has exactly one layer. | Storage `NOT NULL` + `CHECK`; validation |
| L2 | The layer set is closed. Unknown values are rejected. | Enum + storage `CHECK` |
| L3 | `theological_interpretation` requires a non-empty attribution. | Validation rejects |
| L4 | `scripture` requires a named edition and a valid reference. | Validation rejects |
| L5 | `ai_hypothesis` requires provenance of generation (model/method + inputs). | Validation rejects |
| L6 | `ai_hypothesis` output is flagged at every presentation boundary. | Serialisation enforces |
| L7 | No record may be promoted to a stronger layer by relabelling. | Promotion requires evidence + human decision + audit |
| L8 | Layer survives serialisation and deserialisation. | Round-trip tests |
| L9 | Layer survives the Gomine exchange boundary in both directions. | Exchange-format tests |
| L10 | A query may filter by layer; it may never silently merge layers. | Query API requires explicit layer handling |

## 4. Layer strength and promotion

Layers have an ordering of evidential strength:

```
ai_hypothesis  <  theological_interpretation  <  linguistic_observation  <  historical_evidence  <  scripture
     (weakest)                                                                    (strongest, but
                                                                                 only within its
                                                                                 own edition)
```

This ordering is **not** a hierarchy of truth, and it is not a scale on which claims are scored. It expresses
only what kind of warrant a record has.

**Rules:**

1. **Downgrading is always safe.** Reclassifying something as weaker requires no approval.
2. **Upgrading is never safe.** Promotion requires:
   - new evidence that changes the warrant, **and**
   - an explicit human decision by the maintainer, **and**
   - an append-only audit record stating what evidence and what decision.
3. **Relabelling is not promotion.** Changing a stored layer value without evidence and a decision is a
   Critical integrity incident. See [../SECURITY.md](../SECURITY.md).
4. **When uncertain, choose the weakest applicable layer.**
5. **`scripture` is never a promotion target for generated content,** under any circumstances.

## 5. Composition rules

Derived records that combine inputs from multiple layers take the **weakest** layer of their inputs, unless a
stronger warrant is explicitly established and recorded.

- A graph edge inferred from an AI hypothesis is an `ai_hypothesis` edge.
- A cross-reference supported by manuscript evidence is `historical_evidence` or `scripture` as appropriate —
  but only if the support genuinely is manuscript evidence.
- A linguistic claim supported only by a model's judgement is `ai_hypothesis`, however plausible.

## 6. Presentation obligations

1. Any output mixing layers must **visibly distinguish** them.
2. Any output containing `ai_hypothesis` must carry a non-removable flag.
3. No output may present a mixed-layer result set in a way that implies uniform authority.
4. Exports must carry layer information. An export format that cannot represent layers may not be used.

## 7. Common violations

Rejected at review:

- A record persisted with no layer, or with a defaulted layer chosen silently by code.
- `theological_interpretation` stored without attribution.
- Scripture text produced by a model and stored as `scripture`.
- An AI-derived cross-reference stored as `historical_evidence`.
- A query that returns mixed layers with no layer field in the result.
- An export that drops layer information.
- A layer value changed without an audit record.
- "The Bible says X" where the record actually says "edition E reads X".

---

**Related:** [010-source-integrity.md](010-source-integrity.md) ·
[030-research-standards.md](030-research-standards.md) ·
[060-agent-safety.md](060-agent-safety.md) ·
[../docs/architecture/BKB-DATA-001-data-model.md](../docs/architecture/BKB-DATA-001-data-model.md) ·
[../docs/architecture/ADR/ADR-0008-epistemic-layer-typing.md](../docs/architecture/ADR/ADR-0008-epistemic-layer-typing.md)
