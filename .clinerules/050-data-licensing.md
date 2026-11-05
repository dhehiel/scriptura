# 050 — Data Licensing

**Status:** Accepted · **Applies to:** all contributors, agents, and tooling · **Owner:** Maintainer

Licensing errors in this project create legal exposure for every downstream user. The bar is deliberately high.

---

## 1. The governing principle

> **Licensing is dataset-specific. There is no blanket licence for biblical data.**

Not for "the Bible". Not for "ancient Near Eastern texts". Not for an aggregator platform. Not for a parent
collection.

Every individual dataset — and frequently every individual **item** within a dataset — is licensed separately by
its own rights holder. Some aggregators state this explicitly: that each text is licensed separately and there
is no overall licence for the collection. For those sources, an aggregator-level licence establishes **nothing**
about any individual text.

## 2. The two-tier model

| Tier | Material | Licence |
|---|---|---|
| **1** | Scriptura's own code, specifications, schemas, documentation | Apache License 2.0 |
| **2** | Third-party corpus data | Whatever the rights holder applied, per dataset |

**Conflating the tiers is a compliance error.** Scriptura's Apache 2.0 licence covers its own work. It does not
and cannot cover ingested data.

## 3. The ingestion licence gate

**No dataset may be ingested unless all of the following hold.** Enforced by
`src/scriptura/provenance/licensing.py` and tested.

| # | Condition |
|---|---|
| G1 | The dataset has an entry in `docs/data/source-registry.json`. |
| G2 | The dataset has an entry in `docs/data/licence-manifest.json`. |
| G3 | `verification_status` is `verified` — not `unverified`, not `disputed`, not `absent`. |
| G4 | The licence was verified against a **primary source**, with URL and retrieval date recorded. |
| G5 | The verbatim attribution string is recorded, where the licence requires one. |
| G6 | Derivative permission is recorded. |
| G7 | Commercial-use permission is recorded. |
| G8 | Share-alike status is recorded, and its consequences are stated. |
| G9 | The milestone gate for ingestion is open (M0 → M1 requires architecture review). |
| G10 | The maintainer has authorised ingestion **of this dataset**, individually. |

Failure of any condition blocks ingestion. The gate raises; it does not warn.

## 4. Verification standards

1. **Primary source required.** The rights holder's own licence page, licence file, or publication. Not an
   aggregator, mirror, catalogue, forum post, or model recollection.
2. **Record the URL actually used and the retrieval date.**
3. **Record the licence exactly as written.** Name and version. `CC BY 4.0` is not `CC BY`. `CC BY-SA 4.0` is
   not `CC BY`.
4. **Never upgrade a licence.** If the source says CC BY-NC, it is CC BY-NC. Do not record CC BY because that
   would be more convenient.
5. **Never downgrade by assumption either.** "Probably public domain" is not a determination.
6. **Public-domain claims need jurisdiction analysis.** A text may be public domain in most jurisdictions and
   not in others. Record the basis and the jurisdictional caveat.
7. **Composite datasets are licensed in layers.** The underlying text and the added annotation may carry
   different licences. Resolve **both**.
8. **Where a licence cannot be resolved, record `unverified` and do not ingest.** An honest `unverified` entry
   is valuable. A guessed licence is harmful.

## 5. Verification status vocabulary

| Status | Meaning | Ingestible |
|---|---|---|
| `verified` | Licence confirmed against a primary source, URL and date recorded | Yes, with G9 and G10 |
| `unverified` | Candidate source under evaluation; rights not established | **No** |
| `disputed` | Sources conflict, or the licence terms are contested | **No** |
| `restricted` | Licence confirmed but prohibits the intended use | **No** |
| `absent` | No licence information located | **No** |
| `not_required` | Scriptura-authored material; Apache 2.0 applies | n/a |

## 6. Licence consequence rules

### Share-alike (CC BY-SA, and equivalents)

- Derived datasets **inherit** the licence. They are **not** relicensed under Apache 2.0.
- Scriptura must make its derived data available under the same licence.
- The inheritance must be recorded in the manifest and propagated to anything derived from the derivative.
- Scriptura code is not infected by data licensing, but Scriptura **data products** are.

### Non-commercial (CC BY-NC, and equivalents)

- The dataset and its derivatives are **quarantined** from any commercial distribution channel.
- Marked `commercial_use_permitted: false` in the manifest.
- Any Scriptura data product containing such material inherits the restriction.
- Mixing NC material into a permissively-licensed data product is prohibited.

### Attribution (CC BY, CC BY-SA, CC BY-NC)

- The **verbatim** attribution string is recorded in `docs/data/attribution/ATTRIBUTIONS.md`.
- Attribution wording is reproduced exactly. It is not paraphrased, shortened, or "tidied".
- Attribution travels with redistributions and appears in `NOTICE`.

### Public domain

- Record the basis: age of the work, explicit dedication, or jurisdictional analysis.
- Record the jurisdictional caveat where one applies.
- Record whether the *digital edition* carries its own licence distinct from the underlying work. A public-domain
  work may be distributed in an edition whose encoding is separately licensed.

### All rights reserved

- Not ingestible. Record as `restricted` with the reason.
- Do not ingest on the theory that the use is fair. Fair-use analysis is a legal judgement outside this
  project's competence and authority.

## 7. Prohibited practices

1. **Inferring a licence** from a sibling dataset, a parent collection, or an aggregator platform.
2. **Recording a licence without a primary source.**
3. **Upgrading a licence** to something more permissive.
4. **Committing corpus data** to version control, in any directory, at any milestone.
5. **Paraphrasing a mandatory attribution string.**
6. **Relicensing share-alike derivatives** under Apache 2.0.
7. **Mixing NC material** into a permissive data product.
8. **Ingesting before the milestone gate opens,** however ready the code appears.
9. **Treating an `unverified` entry as ingestible** because it "looks freely available".
10. **Deleting or weakening a licence record** to unblock ingestion.

## 8. Machine-readable records

| File | Purpose |
|---|---|
| `docs/data/source-registry.json` | Candidate and approved sources, with availability and `verification_status` |
| `docs/data/licence-manifest.json` | Authoritative licence record per dataset; drives the gate |
| `docs/data/attribution/ATTRIBUTIONS.md` | Verbatim attribution strings |
| `datasets/manifests/*.json` | Per-dataset provenance manifest, once ingestion is authorised |
| `NOTICE` | Human-readable attribution travelling with redistributions |

All are validated against JSON Schema under `schemas/data/`. `make check-licences` runs the gate against both
registries and fails on any inconsistency.

## 9. Incident response

A licence defect is a security incident. See [../SECURITY.md](../SECURITY.md).

Report immediately on discovery of:

- corpus data committed to the repository
- a licence recorded more permissively than the primary source states
- an attribution requirement not reproduced verbatim
- share-alike obligations not propagated to derivatives
- NC material in a permissive data product
- ingestion that proceeded despite a non-`verified` status

Response order: stop the path → identify blast radius → preserve the audit trail → notify downstream → add a
regression test and a `make check` rule.

---

**Related:** [010-source-integrity.md](010-source-integrity.md) ·
[000-project-governance.md](000-project-governance.md) ·
[../docs/data/README.md](../docs/data/README.md) ·
[../docs/architecture/BKB-CORPUS-001-corpus-ingestion.md](../docs/architecture/BKB-CORPUS-001-corpus-ingestion.md) ·
[../docs/architecture/ADR/ADR-0010-licence-gate.md](../docs/architecture/ADR/ADR-0010-licence-gate.md) ·
[../NOTICE](../NOTICE)
