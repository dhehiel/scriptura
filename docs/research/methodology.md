# Research Methodology

Purpose: to state how Scriptura produces, records, and assesses knowledge, so that its output can be evaluated
as research rather than received as assertion.

Normative rules: [.clinerules/010-source-integrity.md](../../.clinerules/010-source-integrity.md),
[.clinerules/030-research-standards.md](../../.clinerules/030-research-standards.md),
[BKB-VERIFY-001](../architecture/BKB-VERIFY-001-verification-framework.md),
[DKF-ARCH-001](../architecture/DKF-ARCH-001-discovery-framework.md).

---

## 1. The standard

> **A contribution that advances capability at the cost of provenance is rejected.**

A feature producing impressive output from unverifiable inputs is a liability. Its output will be trusted by
people who cannot check it.

---

## 2. Method

1. **State the question before the method.** Tooling that cannot say what question it answers produces noise.
2. **Record the method.** Inputs, transformations, code version, parameters. An unreproducible result is not a
   result.
3. **Separate observation from interpretation.** What the data shows and what it means are different records in
   different epistemic layers.
4. **Pre-register evaluation** where a method is being assessed. Define success before running.
5. **Report the baseline.** A method is interesting only relative to what it beats.
6. **Report failures.** A method that works on 70% of cases must say so.

---

## 3. Evidence

| Rule | Detail |
|---|---|
| Primary over secondary | A licence statement from the rights holder is primary; from an aggregator, secondary. Only primary establishes rights. |
| Edition specificity | Never cite "the text". Cite the edition. |
| Dating carries its basis | A date without a stated basis is an assertion. |
| Attribution for interpretation | Always. An unattributed interpretation is rejected at validation. |
| Explicit evidence chains | Each link individually resolvable. |
| Weight is derived, never asserted | Chain strength follows from its links. |

A claim with no evidence chain is `unverified`, **however true it may be**.

---

## 4. Uncertainty

Confidence is a real number in `[0, 1]`, mandatory on derived claims, **derived from the evidence chain**.

Four distinct states, never interchangeable:

| State | Meaning |
|---|---|
| `unknown` | No evidence located |
| `contested` | Evidence exists and points in different directions |
| `weakly_supported` | Some evidence, insufficient for confidence |
| `supported` | Evidence chain sufficient for the stated confidence |

Calibrated language is mandatory. "Proves", "establishes", and "demonstrates" are reserved for demonstrable
entailment. Prefer "supports", "is consistent with", "suggests". Uncertainty is never rounded away: `0.6` is not
"likely".

---

## 5. Disagreement

Disagreement is classified, because the kinds are handled differently.

| Kind | Handling |
|---|---|
| **Edition difference** | Both recorded as `scripture` in their own edition. Claim state `contested`. |
| **Analytical difference** | Both recorded as `linguistic_observation`. Claim state `contested`. |
| **Interpretive difference** | Both recorded as `theological_interpretation`, attributed. `out_of_scope` for verification. |
| **Evidential conflict** | Both recorded as `historical_evidence`. Claim state `contested`. |
| **Doctrinal disagreement** | Recorded with attributions. **Never resolved by Scriptura.** |

Rules: preserve all positions with sources; never average, blend, or select a winner; a "consensus reading" is
itself an interpretive position and must be attributed; **majority is not authority** — record the count, not a
verdict.

---

## 6. Null and negative results

1. Record them. "Searched X for Y and found nothing" is a result.
2. Record what was searched, in enough detail to repeat it.
3. **Absence of evidence is never evidence of absence.** "No manuscript evidence was located" is not "no
   manuscript evidence exists".
4. Null results are first-class records, not omissions from a report.
5. Refuted and dismissed hypotheses are retained, so the same false pattern is not re-proposed indefinitely.

---

## 7. Reproducibility

1. Deterministic by default. Where non-determinism is unavoidable, record the seed and version.
2. Pin dataset version, code version, and parameters.
3. Record the environment where it affects results.
4. A result no one can reproduce is a claim, not a finding.

---

## 8. Domain-specific standards

### Textual criticism

- Witnesses are named; readings are attributed to witnesses.
- Apparatus entries record **variants, not resolutions**.
- Never present a critical text as "the original". Present it as an edition.

### Original languages

- Lemmatisation and parsing are attributed to a dataset or analyst.
- Semantic range claims cite attested usage, not intuition.
- Record the Unicode normalisation form for all original-language text.
- Do not silently transliterate, normalise, or strip diacritics from stored text. Diacritic folding is a
  **search** affordance only.

### Historical context

- Dating, provenance, and identification of material evidence carry their basis and uncertainty.
- Do not import a date from a secondary summary without the primary basis.
- External evidence does not inherit scriptural authority by association.

### Theology

- Every position is attributed to a named tradition or author with a named work.
- "The church fathers" is not an attribution. A named author with a named work is.
- Modern and ancient positions are treated identically.
- Scriptura records positions; it never adopts one.

### Machine-generated content

- Always `ai_hypothesis`. Always flagged. Always carries model, method, inputs, and confidence.
- Never promoted by relabelling.
- Never the sole basis for a downstream authoritative claim.

---

## 9. What Scriptura may and may not assert

| Assertable | Not assertable |
|---|---|
| "Edition E reads X at reference R" | "The Bible says X" (without naming an edition) |
| "Witness W attests reading X" | "The original text read X" |
| "Tradition T holds position P" | "Position P is correct" |
| "Dataset D parses form F as A" | "Form F means A" (without attested usage) |
| "Evidence E dates to D, on basis B" | "No evidence exists for X" |
| "No evidence was located for X, having searched S" | "X is true" on model inference alone |
| "The model infers X, with confidence C" | |

Full list: [BKB-VERIFY-001 §9](../architecture/BKB-VERIFY-001-verification-framework.md).

---

## 10. Research ethics

1. **Respect communities.** Material here is sacred to living communities. Accuracy is a form of respect.
2. **Do not misrepresent a tradition** to make a point or to simplify a data model.
3. **Attribute living scholars** and respect their rights.
4. **Do not use the infrastructure to argue a confessional position** under the cover of neutrality.
5. **Correct your own errors visibly.** A retraction recorded in the changelog is better than a silent fix.

---

## 11. Anti-fabrication

The single most important research rule in this project:

> **Never produce content that looks authoritative but is not.**

A fabricated citation, an invented manuscript siglum, a misattributed quotation, or an unverified licence claim
propagates silently. It is indexed, cross-referenced, cited by downstream agents, and eventually presented to a
researcher who cannot detect it.

**A confident fabrication is worse than an admitted gap. Always. Without exception.**

Full treatment: [.clinerules/010-source-integrity.md](../../.clinerules/010-source-integrity.md).
