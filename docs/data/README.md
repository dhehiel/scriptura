# Dataset Governance

Dataset source registry, licence manifest, and attribution records for Scriptura.

> [!IMPORTANT]
> **No corpus data is present in this repository.** As of M0, no Bible text, translation, lexicon,
> morphological dataset, or any other corpus artefact has been downloaded, vendored, committed, or
> derived. This is machine-checked by `make check`.
>
> The **ingestion gate is CLOSED**. It opens only on a completed architecture review by a human
> reviewer, recorded with identity and date. See
> [../milestones/M0-acceptance-criteria.md](../milestones/M0-acceptance-criteria.md).

---

## Authoritative records

| File | Purpose | Schema |
|---|---|---|
| [source-registry.json](source-registry.json) | Every candidate and approved corpus source, with availability and `verification_status` | [source-registry-entry](../../schemas/data/source-registry-entry.schema.json) |
| [licence-manifest.json](licence-manifest.json) | The authoritative licence record per source; drives the ingestion gate | [licence-record](../../schemas/data/licence-record.schema.json) |
| [attribution/ATTRIBUTIONS.md](attribution/ATTRIBUTIONS.md) | Verbatim attribution strings required by upstream licences | — |
| `../../datasets/manifests/` | Per-dataset provenance manifests, once ingestion is authorised (**empty at M0**) | [dataset-manifest](../../schemas/data/dataset-manifest.schema.json) |
| [../../NOTICE](../../NOTICE) | Human-readable attribution travelling with redistributions | — |

Format is JSON, per [ADR-0003](../architecture/ADR/ADR-0003-json-machine-readable-registries.md): the
registries must be machine-validated by the licence gate using only the standard library, and must be
reviewable in a pull-request diff.

---

## The two-tier licence model

Conflating the tiers is a compliance error.

| Tier | Material | Licence |
|---|---|---|
| **1** | Scriptura's own code, specifications, schemas, documentation | Apache License 2.0 |
| **2** | Third-party corpus data | Whatever the rights holder applied, **per dataset** |

Scriptura's Apache 2.0 licence covers its own work. It does **not** and cannot cover ingested data.

---

## The governing principle

> **Licensing is dataset-specific. There is no blanket licence for biblical data.**

Not for "the Bible". Not for "ancient Near Eastern texts". Not for an aggregator platform. Not for a parent
collection.

This is not a theoretical caution. Two verified findings from the M0 research make it concrete:

**1. Some aggregators state plainly that there is no collection-level licence.** One major source Scriptura
evaluated states in its own licence file: *"Each text is licensed separately, so there is no overall license
for this repository"*, and directs the reader to a per-item `license` field whose value may be any of public
domain, CC0, CC-BY, CC-BY-SA, or **CC-BY-NC**. Citing that platform's terms establishes nothing about any
individual text. Recorded as `src-sefaria-export`.

**2. Some aggregators prohibit the very use Scriptura needs.** Another major source states that its overall
copyright is held by a university, that materials are provided *"for the personal use of students, scholars,
and the public"*, that *"any commercial use or publication without authorization is strictly prohibited"*, and
that materials have *"varying copyright status"*. It is frequently assumed to be an open collection. It is
not. Recorded as `src-perseus-hopper`, status `restricted`.

A third hazard is **layered licensing**: composite datasets frequently license the underlying text under one
licence and the added annotation under another. One Greek morphological dataset Scriptura evaluated states
that its underlying text is subject to one set of terms while *"the morphological parsing and lemmatization is
made available under a CC-BY-SA License"* — without stating a version. Recorded as `src-morphgnt-sblgnt`,
status `disputed`, precisely because the version is unstated and two sources describe the underlying text
licence differently.

---

## Verification status vocabulary

| Status | Meaning | Ingestible |
|---|---|---|
| `verified` | Licence confirmed against a **primary source**, with URL and retrieval date recorded | Not yet — needs an open gate and per-dataset authorisation |
| `unverified` | Candidate source under evaluation; rights **not** established | **No** |
| `disputed` | Sources conflict, or the terms are contested | **No** |
| `restricted` | Licence confirmed but prohibits the intended use | **No** |
| `absent` | No licence information located | **No** |
| `not_required` | Scriptura-authored material; Apache 2.0 applies | n/a |

Two further boolean fields keep the distinction sharp:

- **`licence_cleared`** — licence research is complete and confirmed against a primary source.
- **`ingestible`** — licence cleared **and** the milestone gate is open **and** a human has authorised
  ingestion of this specific dataset.

**At M0 the gate is closed, so `ingestible` is `false` for every entry in the registry.** Licence clearance is
never permission to ingest.

---

## Registry summary at M0

27 sources are recorded. The distribution is the honest result of primary-source research, not a curated list
of what would be convenient.

| Status | Count | Meaning |
|---|---|---|
| `verified` | 5 | Licence confirmed from the rights holder's own statement |
| `disputed` | 1 | Terms contested or incompletely stated |
| `restricted` | 1 | Licence confirmed; prohibits redistribution |
| `unverified` | 7 | Evidence sought; rights not established |
| `absent` | 13 | No licence information located at M0 |

**Ingestible: none.** **Datasets ingested: 0.**

The majority of entries being `unverified` or `absent` is the correct outcome. Recording a guessed licence
would be far worse than recording a gap. See
[.clinerules/010-source-integrity.md](../../.clinerules/010-source-integrity.md).

### Licence-cleared sources

These five have had their licences confirmed against a primary source. **None may be ingested at M0.**

| Source | Licence | Key consequence |
|---|---|---|
| `src-sblgnt` | CC BY 4.0 | Attribution required; exact wording to be confirmed |
| `src-oshb` | CC BY 4.0 | Mandatory verbatim attribution string |
| `src-bsb` | Public domain (dedication 2023-04-30) | No attribution required; recorded voluntarily |
| `src-etcbc-bhsa` | CC BY-NC 4.0 | **Non-commercial quarantine required** |
| `src-stepbible-data` | CC BY 4.0 | Attribution required; does **not** cover embedded modern translations |

### Notable corrections to common assumptions

Recorded because each contradicts something widely believed:

1. **The Berean texts are public domain, not CC-licensed.** They were previously distributed under a Creative
   Commons licence and are still frequently described that way. Their own terms page records an explicit
   public-domain dedication dated 2023-04-30.
2. **The Perseus Hopper is not an open collection.** Overall copyright is held by a university; commercial use
   or publication without authorisation is strictly prohibited; materials have varying status.
3. **A Greek New Testament repository Scriptura evaluated publishes no licence at all.** Its README states
   none and no licence file was found at the repository root. Third-party catalogues attribute a licence to it.
   Absence of a licence statement is **not** a public-domain statement; the legal default is all rights
   reserved.
4. **A morphological dataset's own README describes its underlying text licence differently** from the way the
   text's own licence page describes it.

---

## The ingestion licence gate

Ingestion is permitted only if **all ten conditions** hold. The gate **raises**; it never warns and continues.

| # | Condition |
|---|---|
| G1 | Registry entry present |
| G2 | Manifest entry present |
| G3 | `verification_status` is `verified` |
| G4 | Licence verified against a primary source, with URL and retrieval date |
| G5 | Verbatim attribution recorded where required |
| G6 | Derivative permission recorded |
| G7 | Commercial-use permission recorded |
| G8 | Share-alike status recorded, with consequences |
| G9 | Milestone ingestion gate open |
| G10 | Per-dataset human authorisation |

Implementation: `src/scriptura/provenance/licensing.py`. Specification:
[BKB-CORPUS-001 §4](../architecture/BKB-CORPUS-001-corpus-ingestion.md). Decision record:
[ADR-0010](../architecture/ADR/ADR-0010-licence-gate.md). Rules:
[.clinerules/050-data-licensing.md](../../.clinerules/050-data-licensing.md).

```bash
make check-licences     # registry <-> manifest consistency + gate evaluation
```

---

## Adding a source

1. Open an issue using the
   [dataset addition template](../../.github/ISSUE_TEMPLATE/dataset_addition.yml).
2. Provide **primary-source licence evidence**: the rights holder's own statement, the URL actually used, the
   retrieval date, and a verbatim quotation.
3. Provide edition specificity, rights holder, derivative and commercial status, share-alike status, and any
   jurisdictional caveat.
4. If you cannot find the licence, **say so**. An honest `unverified` entry is valuable; a guessed licence is
   harmful.

Proposals without licence evidence are closed. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## Prohibited practices

| # | Prohibition |
|---|---|
| 1 | Inferring a licence from a sibling dataset, parent collection, or aggregator |
| 2 | Recording a licence without a primary source |
| 3 | Upgrading a licence to something more permissive |
| 4 | Committing corpus bytes to version control |
| 5 | Paraphrasing a mandatory attribution string |
| 6 | Relicensing share-alike derivatives under Apache 2.0 |
| 7 | Mixing non-commercial material into a permissive data product |
| 8 | Ingesting before the milestone gate opens |
| 9 | Treating an `unverified` entry as ingestible |
| 10 | Deleting or weakening a licence record to unblock ingestion |

---

## Disclaimer

Nothing in this directory is legal advice. The records here are the project's good-faith documentation of what
rights holders stated, retrieved on the dates recorded. Rights holders may change their terms. Anyone
redistributing Scriptura data products is responsible for their own compliance.
