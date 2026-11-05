# BKB-CORPUS-001 — Corpus Ingestion

**Biblical Knowledge Base — Corpus Ingestion**

| Field | Value |
|---|---|
| **ID** | BKB-CORPUS-001 |
| **Status** | Accepted |
| **Version** | 1.0.0 |
| **Milestone** | M0 |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Supersedes** | — |

## Abstract

This specification defines how corpus data enters Scriptura: the dataset lifecycle, the licence gate that
precedes any retrieval, the adapter contract, validation rules, provenance capture, integrity checking,
idempotency, rollback, and the on-disk layout of the ingestion workspace. It establishes the standing
prohibition on ingestion before architecture review.

---

## 1. Purpose and scope

### 1.1 Purpose

Ingestion is the point at which Scriptura takes on legal and scholarly responsibility for someone else's data.
This specification ensures that responsibility is discharged deliberately, with rights established **before**
retrieval and provenance captured **at** retrieval.

### 1.2 In scope

Dataset lifecycle; the licence gate; adapter contract; validation; provenance capture; integrity checking;
idempotency; rollback; workspace layout; dataset manifests.

### 1.3 Out of scope

The data model itself ([BKB-DATA-001](BKB-DATA-001-data-model.md)); licence determination policy
([.clinerules/050-data-licensing.md](../../.clinerules/050-data-licensing.md)); verification semantics
([BKB-VERIFY-001](BKB-VERIFY-001-verification-framework.md)).

---

## 2. Standing prohibition

> **At M0, no corpus data is ingested, retrieved, vendored, or committed.**

| # | Prohibition |
|---|---|
| N1 | No dataset is downloaded |
| N2 | No dataset bytes are placed in the repository |
| N3 | No dataset bytes are committed to version control, at any milestone |
| N4 | No dataset adapter is implemented, because no dataset is authorised |
| N5 | No ingestion run is executed |
| N6 | Ingestion does not begin because the code appears ready. Readiness is not authorisation |

Ingestion begins at **M1**, and only when the M0 → M1 gate has opened. That gate requires a completed
architecture review by a human reviewer, recorded with identity and date. See
[../milestones/M0-acceptance-criteria.md](../milestones/M0-acceptance-criteria.md).

Enforcement: `tools/check_repo.py` and `tests/test_repo_hygiene.py` fail if any dataset bytes are present.

---

## 3. Dataset lifecycle

### 3.1 States

```
      ┌──────────┐   licence research    ┌────────────┐
      │ proposed │──────────────────────▶│  vetting   │
      └──────────┘                       └─────┬──────┘
                                               │
                            ┌──────────────────┼──────────────────┐
                            ▼                  ▼                  ▼
                      ┌──────────┐      ┌────────────┐      ┌────────────┐
                      │ verified │      │ unverified │      │ restricted │
                      └────┬─────┘      └────────────┘      └────────────┘
                           │                 │                    │
                           │ gate open +     │ TERMINAL for       │ TERMINAL for
                           │ per-dataset     │ ingestion          │ ingestion
                           │ authorisation   │                    │
                           ▼                 ▼                    ▼
                    ┌────────────┐      (may not ingest)     (may not ingest)
                    │ authorised │
                    └─────┬──────┘
                          ▼
                    ┌────────────┐
                    │ retrieving │
                    └─────┬──────┘
                          ▼
                    ┌────────────┐   fail   ┌──────────┐
                    │ validating │─────────▶│ rejected │
                    └─────┬──────┘          └──────────┘
                          │ pass
                          ▼
                    ┌────────────┐
                    │  ingested  │
                    └─────┬──────┘
                          ▼
                    ┌────────────┐
                    │ superseded │  (a newer version replaces it)
                    └────────────┘
```

### 3.2 State semantics

| State | Meaning | May be retrieved? |
|---|---|---|
| `proposed` | Suggested by a contributor; no licence research done | No |
| `vetting` | Licence research in progress | No |
| `verified` | Licence confirmed against a primary source | Not yet — needs gate + authorisation |
| `unverified` | Rights not established | **No** |
| `disputed` | Sources conflict or terms are contested | **No** |
| `restricted` | Licence confirmed but prohibits the intended use | **No** |
| `absent` | No licence information located | **No** |
| `authorised` | Verified **and** gate open **and** per-dataset human authorisation | Yes |
| `ingested` | Retrieved, validated, loaded, provenance recorded | — |
| `rejected` | Validation failed; not loaded | — |
| `superseded` | Replaced by a newer version; retained for audit | — |

A dataset in any state other than `authorised` **may not be retrieved**. A dataset in any state other than
`verified` **may not become** `authorised`.

---

## 4. The licence gate

### 4.1 Conditions

Ingestion is permitted only if **all** hold. Enforced by `src/scriptura/provenance/licensing.py`; the gate
**raises** rather than warns.

| # | Condition |
|---|---|
| G1 | The dataset has an entry in `docs/data/source-registry.json` |
| G2 | The dataset has an entry in `docs/data/licence-manifest.json` |
| G3 | `verification_status` is `verified` |
| G4 | The licence was verified against a **primary source**, with URL and retrieval date recorded |
| G5 | The verbatim attribution string is recorded where the licence requires one |
| G6 | Derivative permission is recorded |
| G7 | Commercial-use permission is recorded |
| G8 | Share-alike status is recorded and its consequences stated |
| G9 | The milestone gate for ingestion is open |
| G10 | The maintainer has authorised ingestion **of this dataset**, individually |

### 4.2 Gate behaviour

```python
# Normative behaviour
result = gate.evaluate(dataset_id)
if not result.permitted:
    raise LicenceGateError(dataset_id, result.unmet_conditions)   # never proceeds
```

| # | Rule |
|---|---|
| GT1 | The gate is evaluated **before** any network retrieval |
| GT2 | The gate raises on failure. It never warns and continues |
| GT3 | The failure message names **every** unmet condition, not just the first |
| GT4 | The gate cannot be bypassed by configuration, environment variable, or flag |
| GT5 | A gate evaluation is recorded, whether it permitted or refused |
| GT6 | The gate is re-evaluated on every ingestion attempt. A cached permission is not a permission |
| GT7 | The gate lives in `provenance`, not in `ingestion`. A gate inside the thing it gates is not a gate |

### 4.3 Share-alike and non-commercial handling

| Licence property | Consequence at ingestion |
|---|---|
| Share-alike | Derived datasets inherit the licence; recorded on every derived record; **not** relicensed under Apache 2.0 |
| Non-commercial | Dataset and derivatives marked `commercial_use_permitted: false` and quarantined from commercial distribution |
| Attribution required | Verbatim attribution string attached to the dataset and propagated to `NOTICE` |
| No derivatives | Derivation prohibited. If the intended use requires derivation, the dataset is `restricted` |
| All rights reserved | `restricted`. Not ingestible. No fair-use theory is applied |

---

## 5. Adapter contract

### 5.1 Purpose

An adapter converts one upstream dataset's native format into Scriptura's canonical record shape. Adapters are
per-dataset, because formats are per-dataset.

### 5.2 Contract

An adapter must:

| # | Requirement |
|---|---|
| A1 | Declare the `dataset_id` it serves |
| A2 | Declare the input format it accepts, with a version |
| A3 | Accept a path to already-retrieved bytes. **It performs no network I/O** |
| A4 | Yield canonical records, each with layer, reference, provenance, and payload |
| A5 | Record the layer explicitly. **It never defaults a layer** |
| A6 | Compute and attach a content hash per record |
| A7 | Report records it could not convert, with reasons. It never silently drops a record |
| A8 | Be deterministic: same input bytes, same records |
| A9 | Not mutate its input |
| A10 | Not resolve licences. That is the gate's job |
| A11 | Not generate text. It copies |
| A12 | Preserve Unicode exactly, recording the normalisation form |

### 5.3 Why adapters do no network I/O

Separating retrieval from conversion means:

- retrieval can be human-supervised and licence-gated independently;
- conversion is deterministic and reproducible from stored bytes;
- a failed conversion does not leave a partially-retrieved artefact;
- the same bytes can be re-converted by a corrected adapter without re-retrieving.

### 5.4 Adapter status at M0

**No adapter is implemented.** The contract exists at `src/scriptura/ingestion/adapters/base.py`. Implementing an
adapter requires an authorised dataset, which requires an open gate.

---

## 6. Validation

### 6.1 Rules

Every record is validated before loading. A record failing validation is **rejected**, not coerced.

| # | Rule |
|---|---|
| V1 | Schema conformance against the applicable JSON Schema under `schemas/` |
| V2 | Layer present, valid, and in the closed set |
| V3 | Per-layer requirements satisfied (see BKB-DATA-001 §2.2) |
| V4 | Reference valid against the declared canon profile |
| V5 | Provenance complete: `source_uri`, `source_kind`, `content_hash`, `actor`, `created_at` |
| V6 | Content hash matches the content as parsed |
| V7 | Licence reference present and consistent with the dataset's licence record |
| V8 | Identifier unique within its namespace |
| V9 | Unicode valid UTF-8, with normalisation form recorded |
| V10 | No generated text in a `scripture` record |

### 6.2 Failure policy

| # | Rule |
|---|---|
| VF1 | A rejected record is recorded with the reason. It is never silently dropped |
| VF2 | A rejection rate above the dataset's declared threshold fails the whole run |
| VF3 | A run that fails leaves no partially-loaded state. Loading is transactional |
| VF4 | Validation is deterministic and reproducible |
| VF5 | A validator that cannot decide must reject. It must not guess |

---

## 7. Provenance capture

Captured **at retrieval**, not reconstructed later.

| Field | Captured from |
|---|---|
| `source_uri` | The URL actually used |
| `retrieved_at` | The retrieval timestamp |
| `content_hash` | SHA-256 of the bytes as retrieved |
| `byte_length` | Size as retrieved |
| `http_status` or equivalent | The retrieval outcome |
| `licence_id` | The licence record that permitted retrieval |
| `dataset_version` | The upstream version or release identifier |
| `actor` | Who invoked the retrieval |
| `normalisation_form` | The Unicode form of the stored text |

A record without complete provenance is rejected (V5).

---

## 8. Integrity

| # | Rule |
|---|---|
| I1 | The raw bytes as retrieved are hashed before parsing |
| I2 | The hash is recorded on the dataset record and on the ingestion run |
| I3 | Re-ingestion of identical bytes produces identical records |
| I4 | A record whose content does not hash to its recorded digest is a data-integrity incident |
| I5 | Raw bytes are retained in `datasets/raw/` for the duration of the run, and are **never** committed |
| I6 | Where a licence permits retention, raw bytes may be retained locally for reproducibility; where it does not, they are deleted after the run and the deletion is recorded |

---

## 9. Idempotency and re-ingestion

| # | Rule |
|---|---|
| ID1 | Ingestion is idempotent with respect to content-addressable identifiers |
| ID2 | Re-ingesting identical bytes changes nothing |
| ID3 | Re-ingesting different bytes for the same dataset creates a **new** dataset version and supersedes the old; it does not overwrite |
| ID4 | Supersession is recorded in `provenance_events` |
| ID5 | Records from a superseded version are retained for audit unless deletion is authorised |
| ID6 | A partial run may be resumed, but never by skipping validation |

---

## 10. Rollback

| # | Rule |
|---|---|
| R1 | Loading is transactional. A failed run leaves no partial state |
| R2 | Rollback is by a forward migration or a recorded reversal, never by silent deletion |
| R3 | Rolling back an ingestion records the reason and the actor in `provenance_events` |
| R4 | Rollback never removes the licence record or the ingestion run record |
| R5 | Rollback of a `verified` licence determination requires maintainer approval and an ADR |

---

## 11. Workspace layout

```
datasets/
├── raw/            Bytes exactly as retrieved. Never committed. Hashed on arrival.
├── interim/        Parsed but not yet validated. Never committed.
├── processed/      Validated, schema-conformant, licence-cleared. Never committed.
├── manifests/      Per-dataset provenance manifests (JSON). Committed — metadata only.
└── third_party/    Vendored upstream material, only if a licence permits it. Never committed by default.
```

| # | Rule |
|---|---|
| W1 | `raw/`, `interim/`, `processed/`, and `third_party/` are gitignored for all content |
| W2 | Only `manifests/` may hold committed files, and only metadata — never corpus text |
| W3 | Directory structure is preserved by `.gitkeep` files |
| W4 | A manifest is committed **with** its dataset record, not after |
| W5 | No dataset byte may appear anywhere else in the repository |

---

## 12. Dataset manifest

A manifest is the committed, metadata-only record of an ingestion. Schema:
[`schemas/data/dataset-manifest.schema.json`](../../schemas/data/dataset-manifest.schema.json).

| Field | Requirement |
|---|---|
| `dataset_id` | Mandatory |
| `name`, `edition`, `version` | Mandatory |
| `licence_id` | Mandatory |
| `verification_status` | Mandatory; must be `verified` |
| `source_uri` | Mandatory |
| `retrieved_at` | Mandatory |
| `content_hash` | Mandatory — SHA-256 of the retrieved bytes |
| `byte_length` | Mandatory |
| `record_count` | Mandatory |
| `rejected_count` | Mandatory |
| `adapter`, `adapter_version` | Mandatory |
| `normalisation_form` | Mandatory for original-language text |
| `attribution` | Verbatim string where required |
| `derivative_of` | Where derived |
| `share_alike_inherited` | Where applicable |
| `commercial_use_permitted` | Mandatory |
| `authorised_by`, `authorised_at` | Mandatory — the human authorisation |
| `ingestion_run_id` | Mandatory |

A manifest **never contains corpus text**. It is metadata about the corpus.

---

## 13. Prohibitions

Consolidated. Each is checked by `make check` or `make test`.

| # | Prohibition |
|---|---|
| P1 | Retrieving before the gate permits |
| P2 | Committing corpus bytes |
| P3 | Defaulting a layer in an adapter |
| P4 | Generating text in a `scripture` record |
| P5 | Silently dropping a record that failed to convert |
| P6 | Loading without validation |
| P7 | Partial loading outside a transaction |
| P8 | Overwriting an existing dataset version |
| P9 | Silent deletion of provenance |
| P10 | Upgrading a licence to unblock ingestion |
| P11 | Paraphrasing a mandatory attribution string |
| P12 | Relicensing share-alike derivatives under Apache 2.0 |
| P13 | Network I/O inside an adapter |
| P14 | Bypassing the gate by configuration or flag |

---

## 14. Verification

| Check | Command |
|---|---|
| Licence gate refuses non-`verified` | `python -m unittest tests.test_licensing` |
| Gate names every unmet condition | `python -m unittest tests.test_licensing` |
| Gate cannot be bypassed | `python -m unittest tests.test_licensing` |
| Registry and manifest schema conformance | `python -m unittest tests.test_schemas` |
| Registry ↔ manifest consistency | `make check-licences` |
| No corpus data present | `make check`, `python -m unittest tests.test_repo_hygiene` |
| Ingestion framework refuses unauthorised dataset | `python -m unittest tests.test_ingestion` |
| Full suite | `make test` |

---

## 15. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.0.0 | M0 | Initial specification: dataset lifecycle, licence gate, adapter contract, validation, provenance capture, integrity, idempotency, rollback, workspace layout, manifest format. | ADR-0010 |
