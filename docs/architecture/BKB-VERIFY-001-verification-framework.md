# BKB-VERIFY-001 — Verification Framework

**Biblical Knowledge Base — Verification Framework**

| Field | Value |
|---|---|
| **ID** | BKB-VERIFY-001 |
| **Status** | Accepted |
| **Version** | 1.0.0 |
| **Milestone** | M0 |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Supersedes** | — |

## Abstract

This specification defines how Scriptura verifies claims: verification states, evidence chains, confidence
representation, the treatment of disagreement, verification checks and their determinism, the audit trail, and
the rules governing what may and may not be asserted. It establishes that verification is a property of a claim
together with its evidence chain, not a property of the claim in isolation.

---

## 1. Purpose and scope

### 1.1 Purpose

A biblical research system that cannot distinguish what it has verified from what it has merely collected is
indistinguishable from a pile of text. This specification makes verification a first-class, queryable,
auditable property.

### 1.2 In scope

Verification states; evidence chains; confidence; disagreement; checks and determinism; audit; assertion rules.

### 1.3 Out of scope

The layer model ([BKB-DATA-001](BKB-DATA-001-data-model.md)); hypothesis generation
([DKF-ARCH-001](DKF-ARCH-001-discovery-framework.md)); agent contracts
([BKB-AGENTS-001](BKB-AGENTS-001-agent-framework.md)).

---

## 2. Core principle

> **Verification is a property of a claim together with its evidence chain — never of a claim in isolation.**

A claim is not "verified" because it is plausible, widely held, or consistent with other claims. It is verified
when a specific, resolvable chain of evidence supports it, and the strength of the verification is the strength
of that chain.

Corollary: **a claim with no evidence chain is unverified, however true it may be.**

---

## 3. Verification states

| State | Definition | Requirements |
|---|---|---|
| `unverified` | No evidence chain recorded | Default state for every new claim |
| `weakly_supported` | Some evidence exists; insufficient for the stated confidence | ≥1 evidence link, each resolvable |
| `supported` | Evidence chain sufficient for the stated confidence | Chain complete, each link resolvable, confidence calibrated |
| `contested` | Evidence exists and points in different directions | All competing positions recorded with sources |
| `refuted` | Evidence contradicts the claim | Contradicting evidence recorded |
| `unknown` | No evidence located, and the search is recorded | Search recorded with enough detail to repeat it |
| `out_of_scope` | Not a verifiable claim | Reason recorded — e.g. a doctrinal position, which Scriptura does not adjudicate |

### 3.1 State rules

| # | Rule |
|---|---|
| VS1 | `unverified` is the default. Nothing begins verified |
| VS2 | A state change requires a recorded evidence change and an actor |
| VS3 | `contested` requires **all** competing positions to be recorded, not merely an acknowledgement that they exist |
| VS4 | `refuted` never deletes the claim. The claim and the refutation coexist |
| VS5 | `unknown` requires a recorded search. "No evidence located" is not "no evidence exists" |
| VS6 | `out_of_scope` is not a verdict. It records that Scriptura does not adjudicate the question |
| VS7 | A state is never inferred silently. It is set explicitly |
| VS8 | States are never averaged across claims |

### 3.2 Doctrinal questions

Claims that are doctrinal or canonical in nature are recorded as `out_of_scope` for verification, with the
competing positions recorded as `theological_interpretation` records attributed to their traditions. Scriptura
records positions; it does not adjudicate them.

---

## 4. Evidence chains

### 4.1 Structure

An evidence chain is an ordered list of links. Each link is:

| Field | Requirement |
|---|---|
| `link_id` | Mandatory |
| `evidence_id` | The evidence record supporting this link |
| `layer` | The evidence's epistemic layer |
| `relation` | How this evidence bears on the claim: `supports`, `contradicts`, `qualifies`, `contextualises` |
| `weight` | Optional, derived — never asserted |
| `source_uri` | Resolvable locator |
| `content_hash` | Digest of the evidence as consulted |
| `consulted_at` | When |
| `source_kind` | `primary` or `secondary` |

### 4.2 Chain rules

| # | Rule |
|---|---|
| EC1 | Every link is individually resolvable by a third party |
| EC2 | A chain with an unresolvable link is not a chain. The claim is `unverified` |
| EC3 | A chain records `contradicts` links. A chain containing only `supports` links, where contradicting evidence is known to exist, is **incomplete** and the claim may not be `supported` |
| EC4 | Chain strength is **derived** from its links. It is never asserted |
| EC5 | A chain's strength cannot exceed the strength of its weakest load-bearing link |
| EC6 | A `secondary`-only chain caps the claim at `weakly_supported` unless a primary link is added |
| EC7 | A chain containing an `ai_hypothesis` link cannot support a claim above `weakly_supported` |
| EC8 | Chains are append-only. Correction is by appending |
| EC9 | A chain is reproducible: the same links, consulted again, yield the same assessment |

### 4.3 Evidence strength by layer

| Layer | Can support | Cannot support |
|---|---|---|
| `scripture` | What a named edition attests | What "the original" said; what is historically true |
| `historical_evidence` | External facts, with dating basis | Doctrinal claims |
| `linguistic_observation` | Attested usage and analysis | Authorial intent as fact |
| `theological_interpretation` | That a tradition holds a position | That the position is correct |
| `ai_hypothesis` | Nothing above `weakly_supported` | Any authoritative claim |

This table is normative. A claim whose evidence chain cannot support its asserted state is **not** in that state,
regardless of what is recorded.

---

## 5. Confidence

### 5.1 Representation

| # | Rule |
|---|---|
| C1 | Confidence is a real number in `[0, 1]`, mandatory on derived claims |
| C2 | Confidence is **derived from the evidence chain**, not asserted |
| C3 | Confidence is never rounded away. `0.6` is not "likely" |
| C4 | Confidence is never presented without its basis |
| C5 | Calibrated language is mandatory: "proves", "establishes", "demonstrates" are reserved for demonstrable entailment. Prefer "supports", "is consistent with", "suggests" |
| C6 | Confidence is per-claim. There is no global or per-dataset confidence |
| C7 | An `ai_hypothesis` confidence reflects the model's own assessment and is **not** evidence of truth |
| C8 | Confidence does not survive a change of evidence chain without recomputation |

### 5.2 Distinct states

Confidence is not the only uncertainty representation. Four states are distinct and are not interchangeable:

| State | Meaning |
|---|---|
| `unknown` | No evidence located |
| `contested` | Evidence exists and points in different directions |
| `weakly_supported` | Some evidence, insufficient for confidence |
| `supported` | Evidence chain sufficient for the stated confidence |

A high confidence in a `contested` claim is a contradiction and is rejected at validation.

---

## 6. Disagreement

### 6.1 Classification

Disagreement must be classified, because the kinds are handled differently.

| Kind | Definition | Handling |
|---|---|---|
| **Edition difference** | Different editions read differently | Both recorded as `scripture` in their own edition. Claim state: `contested` |
| **Analytical difference** | Different datasets or scholars parse differently | Both recorded as `linguistic_observation`. Claim state: `contested` |
| **Interpretive difference** | Different traditions read differently | Both recorded as `theological_interpretation`, attributed. Claim state: `out_of_scope` for verification |
| **Evidential conflict** | External evidence points in different directions | Both recorded as `historical_evidence`. Claim state: `contested` |
| **Doctrinal disagreement** | Communities hold incompatible doctrines | Recorded with attributions. **Never resolved by Scriptura** |

### 6.2 Rules

| # | Rule |
|---|---|
| D1 | Preserve all positions with their sources |
| D2 | Do not average, blend, or select a winner |
| D3 | A "consensus reading" is itself an interpretive position and must be attributed to whoever holds it |
| D4 | **Majority is not authority.** A reading held by more witnesses is not thereby correct. Record the count; do not record a verdict |
| D5 | Do not silently drop a position |
| D6 | Do not resolve a doctrinal or canonical disagreement |
| D7 | A well-sourced minority position is recorded with the same fidelity as a majority one |

---

## 7. Verification checks

### 7.1 Check contract

A verification check is a deterministic function over a claim and its evidence chain, producing a result
conforming to [`schemas/verification/verification-result.schema.json`](../../schemas/verification/verification-result.schema.json).

| # | Requirement |
|---|---|
| CK1 | Deterministic. Same inputs, same result |
| CK2 | Reproducible. Records code version and parameters |
| CK3 | Returns a structured result, not a boolean |
| CK4 | Reports what it checked and what it could not check |
| CK5 | Never mutates the claim or its evidence |
| CK6 | Never resolves disagreement |
| CK7 | Never promotes a layer |
| CK8 | Records its own identity and version in the result |

### 7.2 Baseline check set

| Check | What it verifies |
|---|---|
| `citation_resolvable` | Every `source_uri` in the chain resolves |
| `content_hash_matches` | Evidence content matches its recorded digest |
| `layer_requirements_met` | Per-layer requirements satisfied (BKB-DATA-001 §2.2) |
| `reference_valid` | Reference valid against the declared canon profile |
| `licence_present` | A licence record governs any dataset-derived evidence |
| `licence_verified` | The licence `verification_status` is `verified` |
| `chain_complete` | No unresolvable links; contradicting evidence included where known |
| `confidence_calibrated` | Confidence consistent with chain strength and state |
| `attribution_present` | `theological_interpretation` carries an attribution |
| `flag_present` | `ai_hypothesis` carries `non_authoritative` |
| `provenance_complete` | Provenance fields complete |
| `state_consistent` | Verification state consistent with the evidence chain |

### 7.3 Result shape

| Field | Requirement |
|---|---|
| `check_id`, `check_version` | Mandatory |
| `claim_id` | Mandatory |
| `passed` | Mandatory — but a `false` is not a deletion |
| `severity` | `info`, `warning`, `error`, `blocking` |
| `details` | What was checked |
| `uncheckable` | What could not be checked, and why |
| `ran_at`, `code_version` | Mandatory |

A check that cannot decide must report `uncheckable`. It must not guess, and must not silently pass.

---

## 8. Audit

| # | Rule |
|---|---|
| A1 | Every verification state change is recorded in `provenance_events` |
| A2 | Every check result is retained |
| A3 | Every evidence chain link is append-only |
| A4 | Audit records carry actor and timestamp |
| A5 | Audit records are never silently deleted |
| A6 | A state change without an evidence change is an integrity incident |
| A7 | A layer promotion requires evidence, reasoning, actor, and date — enforced by a `CHECK` constraint |

---

## 9. Assertion rules

What Scriptura may and may not assert.

| # | Rule |
|---|---|
| AS1 | "Edition E reads X at reference R" — assertable, with the edition named |
| AS2 | "The Bible says X" — **not assertable** unless a specific edition is named |
| AS3 | "Witness W attests reading X" — assertable, with the witness named |
| AS4 | "The original text read X" — **not assertable.** An edition's reconstruction is an edition's reconstruction |
| AS5 | "Tradition T holds position P" — assertable, attributed |
| AS6 | "Position P is correct" — **not assertable** |
| AS7 | "Dataset D parses form F as A" — assertable, with the dataset named |
| AS8 | "Form F means A" — **not assertable** without attested usage |
| AS9 | "Evidence E dates to D" — assertable, with basis and uncertainty |
| AS10 | "No evidence was located for X" — assertable, with the search recorded |
| AS11 | "No evidence exists for X" — **not assertable** |
| AS12 | "The model infers X" — assertable, flagged, with confidence |
| AS13 | "X is true" on the basis of model inference alone — **not assertable** |

These rules are enforced at review and, where expressible, by validation.

---

## 10. Verification at M0

At M0 there is no corpus, so no claim is verified. What exists is the framework:

| Deliverable | Status |
|---|---|
| Verification states | Specified |
| Evidence chain structure | Specified and schema-defined |
| Confidence rules | Specified |
| Disagreement classification | Specified |
| Check contract | Specified |
| Baseline check set | Specified |
| Audit requirements | Specified; `provenance_events` table exists |
| Check implementations | **Not implemented** — no claims exist to check |

Implementation of the check set is scheduled for **M4**, when there is a corpus to verify against. See
[../milestones/ROADMAP.md](../milestones/ROADMAP.md).

---

## 11. Prohibitions

| # | Prohibition |
|---|---|
| P1 | Marking a claim verified without an evidence chain |
| P2 | Asserting a state the evidence chain cannot support |
| P3 | Omitting known contradicting evidence from a chain |
| P4 | Resolving a doctrinal or canonical disagreement |
| P5 | Treating majority as authority |
| P6 | Silently dropping a competing position |
| P7 | Rounding away uncertainty |
| P8 | Presenting confidence without its basis |
| P9 | A check that guesses instead of reporting `uncheckable` |
| P10 | Deleting a refuted claim |
| P11 | Writing absence of evidence as evidence of absence |
| P12 | Promoting a layer as a side effect of verification |

---

## 12. Verification of this specification

| Check | Command |
|---|---|
| Verification result schema is valid | `python -m unittest tests.test_schemas` |
| Promotion audit constraint enforced | `python -m unittest tests.test_storage` |
| Layer requirements enforced | `python -m unittest tests.test_layers` |
| Licence gate refuses unverified | `python -m unittest tests.test_licensing` |
| Full suite | `make test` |

---

## 13. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.0.0 | M0 | Initial specification: verification states, evidence chains, confidence, disagreement classification, check contract, baseline check set, audit, assertion rules. Check implementations deferred to M4. | ADR-0008 |
