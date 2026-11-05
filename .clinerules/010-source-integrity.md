# 010 — Source Integrity

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

This is the most important rule file in the project.

---

## 1. The cardinal rule

> **Never produce content that looks authoritative but is not.**

A fabricated citation, an invented identifier, a misattributed quotation, or an unverified licence claim is not
a small error in this domain. It propagates: it is indexed, cross-referenced, cited by downstream agents, and
eventually presented to a researcher with no means of detecting it.

**A confident fabrication is worse than an admitted gap. Always. Without exception.**

## 2. Citation rules

1. **Cite the source, not the recollection.** A citation is a resolvable locator:
   - a URL,
   - a DOI,
   - an edition with book/chapter/verse,
   - a file path plus line number,
   - a dataset identifier plus record identifier.

   "It is generally known that...", "scholars agree that...", and "traditionally..." are **not** citations. They
   are unsourced assertions and must be either sourced or removed.

2. **A citation must be resolvable by a third party.** If no one else can follow it to the same source, it is
   not a citation.

3. **Never invent identifiers.** Manuscript sigla, DOI strings, catalogue numbers, shelf marks, edition
   designations, dataset identifiers, and version strings must be **copied from a source**, never constructed
   by pattern. Constructing a plausible-looking DOI from a known prefix is fabrication.

4. **Record retrieval, including failure.** For any external source consulted, record the URL, the retrieval
   date, and what was actually found. **A failed fetch is a result and must be recorded as one.** Do not
   substitute remembered content for content that failed to load.

5. **Distinguish primary from secondary.**
   - **Primary:** the rights holder's own licence page; the edition itself; the publication.
   - **Secondary:** an aggregator, a mirror, a catalogue, a summary, a model's recollection.

   A licence determination requires a primary source. A secondary source may justify further investigation; it
   never establishes rights.

6. **Version and edition specificity.** "The Greek New Testament" is not a source. Which edition, which
   printing, which release? Record it.

## 3. Quotation rules

1. **Quote verbatim inside quotation marks.** Do not paraphrase inside quotes.
2. **Do not silently normalise** orthography, punctuation, capitalisation, or diacritics inside a quotation. If
   normalisation is applied for a stated technical purpose, say so explicitly.
3. **Mark elisions** with a standard ellipsis convention. Do not elide in a way that changes meaning.
4. **Preserve original-language text exactly,** including direction, combining marks, and normalisation form.
   Record the Unicode normalisation form used.
5. **Attribution is mandatory** for every quotation. A quotation with no attributed source is rejected.

## 4. Provenance rules

1. **Every persisted record carries provenance:** source, retrieval date, and a content hash.
2. **Provenance is append-only.** Provenance records are never silently mutated or deleted. Correction is by
   appending a new record that supersedes the old one, with the reason recorded.
3. **Content must match its recorded hash.** A record whose text does not hash to its recorded digest is a
   data-integrity incident. See [../SECURITY.md](../SECURITY.md).
4. **Derived records record their derivation.** What inputs, what transformation, what version of the code.
5. **No orphan records.** A record with no resolvable provenance may not be persisted.

## 5. Anti-fabrication rules

Prohibited absolutely:

1. **Generating scripture text.** Scripture-layer content is always sourced from a named edition present in the
   corpus. An agent may never produce scripture text from memory or from a model.
2. **Inventing manuscript readings, sigla, or variant apparatus.**
3. **Inventing quotations** from ancient authors, translators, commentators, or lexica.
4. **Inventing licences** or licence terms.
5. **Inventing availability.** "This dataset is freely downloadable" must be verified, not assumed. If access
   is gated, paywalled, or unavailable, say so.
6. **Presenting inference as finding.** Anything generated is `ai_hypothesis` until evidence makes it stronger.
7. **Padding a gap with plausible content.** An empty result is a valid result.
8. **Citing a source you did not read.** Citing a source because a secondary source mentioned it is acceptable
   **only** if you state that you are citing it second-hand.

## 6. Handling disagreement between sources

1. **Preserve both positions** with their sources.
2. **Do not average** them, do not pick the more convenient one, do not silently drop one.
3. **Record the nature of the disagreement:** factual conflict, interpretive difference, edition difference, or
   scope difference. These are different things and are handled differently.
4. **Never resolve a doctrinal or canonical disagreement.** Record it with attributions.

## 7. Null and negative results

1. **Record them.** "Searched X for Y and found nothing" is a valuable result.
2. **Never write absence of evidence as evidence of absence.** "No manuscript evidence was located" is not
   "no manuscript evidence exists".
3. **Record what was searched,** with enough detail that the search could be repeated.

## 8. Uncertainty

1. **Represent it.** A confidence value is mandatory on derived claims.
2. **Never hide it** behind assertive phrasing.
3. **Distinguish** *unknown*, *contested*, and *unlikely*. These are different states.
4. **Do not round uncertainty away.** A 60% confidence is not "likely".

## 9. Verification before assertion

Before asserting any of the following, verify against a primary source or record it as unverified:

- a licence or licence term
- the availability or accessibility of a dataset
- the existence, date, or content of a manuscript or edition
- the wording of a quotation
- the identity of a rights holder
- the provenance of a text

Where verification is impossible in the current environment, **record the claim as `unverified` and state what
verification would require.** An `unverified` marker is an honest artefact. A confident guess is a defect.

## 10. Self-check before submission **[human review]**

Before submitting any contribution, confirm:

- [ ] Every factual claim resolves to a citation.
- [ ] Every quotation is verbatim and attributed.
- [ ] Every licence statement traces to a primary source, or is marked `unverified`.
- [ ] Every identifier was copied, not constructed.
- [ ] No scripture text was generated rather than sourced.
- [ ] No inference is presented without its `ai_hypothesis` flag.
- [ ] Disagreements are preserved, not resolved.
- [ ] Null results are recorded as null.
- [ ] Uncertainty is represented, not hidden.
- [ ] Nothing is claimed that was not performed and verified.

---

**Related:** [020-epistemic-layers.md](020-epistemic-layers.md) ·
[030-research-standards.md](030-research-standards.md) ·
[050-data-licensing.md](050-data-licensing.md) ·
[../AGENTS.md](../AGENTS.md) · [../SECURITY.md](../SECURITY.md) ·
[../docs/architecture/BKB-VERIFY-001-verification-framework.md](../docs/architecture/BKB-VERIFY-001-verification-framework.md)
