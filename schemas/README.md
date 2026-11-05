# JSON Schemas

Machine-readable schema definitions for Scriptura's data structures.

All documents are **JSON Schema draft 2020-12**. They are normative: an implementation that produces a document
failing its schema is defective.

---

## Index

### `core/` — the vocabulary everything else speaks

| Schema | Governs | Normative source |
|---|---|---|
| [core/epistemic-layer.schema.json](core/epistemic-layer.schema.json) | The closed set of five epistemic layers | BKB-DATA-001 §2 |
| [core/reference.schema.json](core/reference.schema.json) | Canonical Bible references | BKB-DATA-001 §3 |
| [core/provenance.schema.json](core/provenance.schema.json) | Provenance; no orphan records | BKB-DATA-001 §4 |
| [core/claim.schema.json](core/claim.schema.json) | Claim-bearing records | BKB-DATA-001 §2, §9 |
| [core/evidence.schema.json](core/evidence.schema.json) | Evidence chain links | BKB-VERIFY-001 §4 |
| [core/edge.schema.json](core/edge.schema.json) | Knowledge graph edges | BKB-DATA-001 §6.5 |

### `data/` — dataset governance

| Schema | Governs | Normative source |
|---|---|---|
| [data/source-registry-entry.schema.json](data/source-registry-entry.schema.json) | Candidate and approved corpus sources | BKB-CORPUS-001 §3–4 |
| [data/licence-record.schema.json](data/licence-record.schema.json) | Authoritative licence records; drive the gate | .clinerules/050, ADR-0010 |
| [data/dataset-manifest.schema.json](data/dataset-manifest.schema.json) | Per-ingestion provenance manifest | BKB-CORPUS-001 §12 |

### `agents/` — declarative agent contracts

| Schema | Governs | Normative source |
|---|---|---|
| [agents/agent-spec.schema.json](agents/agent-spec.schema.json) | Agent specifications. **Nothing executes at M0.** | BKB-AGENTS-001 §4–5 |
| [agents/agent-run.schema.json](agents/agent-run.schema.json) | Append-only agent run records | BKB-AGENTS-001 §8 |

### `verification/` — verification results

| Schema | Governs | Normative source |
|---|---|---|
| [verification/verification-result.schema.json](verification/verification-result.schema.json) | Verification check results | BKB-VERIFY-001 §7 |

---

## Design rules

| # | Rule |
|---|---|
| 1 | Every schema change ships in the same change as the code or data it governs |
| 2 | `additionalProperties: false` by default. Unknown fields are rejected |
| 3 | No implicit defaults for anything semantically significant — especially `layer` |
| 4 | Enumerations are closed. Adding a value requires an accepted ADR |
| 5 | Mandatory fields are listed in `required`. A schema that makes provenance optional is defective |
| 6 | Every schema carries a `description` naming its normative source |
| 7 | Schemas are validated in CI by `make check` and `tests/test_schemas.py` |

---

## Validation

Scriptura validates these schemas with a **stdlib JSON Schema subset validator** at
`src/scriptura/schemas/validator.py`. This is required by
[ADR-0002](../docs/architecture/ADR/ADR-0002-stdlib-only-m0-runtime.md): no third-party validator may be a
mandatory dependency, and none is installable in the reference environment.

### Supported keyword subset

| Keyword | Supported |
|---|---|
| `type` (including type arrays and `null`) | Yes |
| `enum` | Yes |
| `const` | Yes |
| `properties` | Yes |
| `required` | Yes |
| `additionalProperties` (`false` and schema) | Yes |
| `items` | Yes |
| `minLength`, `maxLength` | Yes |
| `minimum`, `maximum` | Yes |
| `pattern` | Yes |
| `$ref` (relative, file-local resolution) | Yes |
| `minItems`, `maxItems` | Yes |
| `allOf`, `anyOf`, `oneOf` | **No** — rejected as unsupported, not silently ignored |
| `if` / `then` / `else` | **No** |
| `$defs` | **No** |

**Unsupported keywords are reported as errors, never silently skipped.** A schema using an unsupported keyword
fails validation rather than appearing to pass. Cross-field invariants that JSON Schema cannot express — for
example "`ingestible` may be true only where `verification_status` is `verified`" — are enforced in
`src/scriptura/provenance/licensing.py` and `tools/check_licences.py`, and documented in the schema description.

Schema documents remain **standard JSON Schema**, so external tooling (`ajv`, `jsonschema`, `check-jsonschema`)
can validate them fully. The subset validator is Scriptura's internal enforcement, not a restriction on the
format.

---

## Verifying

```bash
make check-schemas                              # all schemas parse and are self-consistent
python -m unittest tests.test_schemas           # schemas valid; registries conform
python -m unittest tests.test_schemas_subset    # validator behaviour, including unsupported-keyword rejection
```
