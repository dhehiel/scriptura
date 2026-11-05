# 030 — Research Standards

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

Scriptura is a research instrument. It is held to research standards, not product standards.

---

## 1. The standard

> **A contribution that advances capability at the cost of provenance is rejected.**

A feature that produces impressive output from unverifiable inputs is a liability, not an asset. In this domain
the output will be trusted by people who cannot check it.

## 2. Methodology obligations

1. **State the question before the method.** Research tooling that cannot say what question it answers produces
   noise.
2. **Record the method.** Inputs, transformations, code version, parameters. A result that cannot be reproduced
   is not a result.
3. **Separate observation from interpretation.** What the data shows and what it means are different records in
   different layers.
4. **Pre-register evaluation** where a method is being assessed. Define what counts as success before running it.
5. **Report the baseline.** A method is only interesting relative to what it beats.
6. **Record failures.** A method that works on 70% of cases must say so. A method reported without its failure
   rate is a misrepresentation.

## 3. Evidence standards

1. **Primary over secondary.** See [010-source-integrity.md](010-source-integrity.md) §2.
2. **Edition specificity.** Never cite "the text"; cite the edition.
3. **Dating carries its basis.** A date without a stated basis is an assertion.
4. **Attribution for interpretation.** Always.
5. **Evidence chains are explicit.** A conclusion records the chain of evidence that supports it, and each link
   is individually resolvable.
6. **Weight is not asserted, it is derived.** The strength of a claim follows from its evidence chain, not from
   the confidence of its author.

## 4. Uncertainty

1. **Mandatory on derived claims.** A confidence value is required.
2. **Calibrated language.** Do not use "proves", "establishes", or "demonstrates" for anything short of
   demonstrable entailment. Prefer "supports", "is consistent with", "suggests".
3. **Distinguish four states:**
   | State | Meaning |
   |---|---|
   | `unknown` | No evidence located |
   | `contested` | Evidence exists and points in different directions |
   | `weakly_supported` | Some evidence, insufficient for confidence |
   | `supported` | Evidence chain sufficient for the stated confidence |

4. **Do not round uncertainty away.** 0.6 is not "likely".
5. **Do not represent uncertainty as absence.** "We do not know" ≠ "there is none".

## 5. Disagreement

1. **Preserve it.** Competing readings, analyses, and interpretations are stored together with their sources.
2. **Classify the kind of disagreement:**
   - **Edition difference** — different editions read differently. Both are `scripture` in their own edition.
   - **Analytical difference** — different datasets or scholars parse differently. Both are
     `linguistic_observation`.
   - **Interpretive difference** — different traditions read differently. Both are
     `theological_interpretation`, attributed.
   - **Evidential conflict** — external evidence points in different directions. Both are
     `historical_evidence`.
   - **Doctrinal disagreement** — **never resolved by Scriptura.** Recorded with attributions.

3. **Do not average, blend, or pick a winner.** A "consensus reading" is itself an interpretive position and
   must be attributed to whoever holds it.
4. **Majority is not authority.** A reading held by more witnesses is not thereby correct. Record the count;
   do not record a verdict.

## 6. Null and negative results

1. **Record them.** A search that found nothing is a result.
2. **Record what was searched,** with enough detail to repeat it.
3. **Absence of evidence is never evidence of absence.** This is a standing rule, not a caveat.
4. **Null results are first-class records,** not omissions from a report.

## 7. Reproducibility

1. **Deterministic by default.** Same inputs, same version, same result. Where non-determinism is unavoidable
   (for example a stochastic model), record the seed and the version.
2. **Pin everything.** Dataset version, code version, parameters.
3. **Record the environment** where it affects results.
4. **A result no one can reproduce is a claim, not a finding.**

## 8. Evaluation

1. **Benchmarks are versioned and provenanced** like any other dataset.
2. **Evaluation datasets record their own licensing.** They are datasets.
3. **Report per-case results,** not only aggregates. Aggregates hide failure modes.
4. **Report on the hard cases.** A benchmark chosen because the method passes it is not an evaluation.
5. **Negative evaluation results are published.** See §6.

## 9. Domain-specific standards

### Textual criticism

- Witnesses are named. Readings are attributed to witnesses.
- Apparatus entries record variants, not resolutions.
- Do not present a critical text as "the original". Present it as an edition.

### Original languages

- Lemmatisation and parsing are attributed to a dataset or analyst.
- Semantic range claims cite attested usage, not intuition.
- Record the Unicode normalisation form for all original-language text.
- Do not silently transliterate.

### Historical context

- Dating, provenance, and identification of material evidence carry their basis and uncertainty.
- Do not import a date from a secondary summary without the primary basis.

### Theology

- Every position is attributed to a named tradition or author with a named work.
- Modern and ancient positions are treated identically.
- Scriptura records positions; it never adopts one.

### Machine-generated content

- Always `ai_hypothesis`.
- Always flagged.
- Always carries model, method, inputs, and confidence.
- Never promoted by relabelling.

## 10. Research ethics

1. **Respect communities.** Material here is sacred to living communities. Accuracy is a form of respect.
2. **Do not misrepresent a tradition** to make a point or to simplify a data model.
3. **Attribute living scholars** and respect their rights.
4. **Do not use the infrastructure to argue a confessional position** under the cover of neutrality.
5. **Correct your own errors visibly.** A retraction recorded in the changelog is better than a silent fix.

---

**Related:** [010-source-integrity.md](010-source-integrity.md) ·
[020-epistemic-layers.md](020-epistemic-layers.md) ·
[../docs/research/methodology.md](../docs/research/methodology.md) ·
[../docs/architecture/BKB-VERIFY-001-verification-framework.md](../docs/architecture/BKB-VERIFY-001-verification-framework.md) ·
[../docs/architecture/DKF-ARCH-001-discovery-framework.md](../docs/architecture/DKF-ARCH-001-discovery-framework.md)
