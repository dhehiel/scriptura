# ADR-0003 — JSON for machine-readable registries

| Field | Value |
|---|---|
| **ID** | ADR-0003 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-CORPUS-001 §12; docs/data/ |
| **Supersedes** | — |

## Context

The dataset source registry and the licence manifest must be:

- machine-readable and machine-validated, because the ingestion licence gate reads them;
- human-readable and reviewable, because licence determinations are reviewed by people;
- diffable in version control, because a licence change is a governance event;
- validatable in the reference environment, which has no package-index access (ADR-0002).

YAML is the conventional choice for such files and is more pleasant to hand-edit. However, YAML requires a
third-party parser in Python. Under ADR-0002 that parser cannot be a mandatory dependency, and it is not
installable in the reference environment — so a YAML registry could not be validated, and an unvalidated
licence manifest would defeat the purpose of the gate.

YAML also carries well-known hazards: implicit type coercion (the classic Norway problem, where `NO` parses as a
boolean), duplicate-key behaviour, and anchor/alias expansion. For a file whose contents determine legal
compliance, implicit coercion is unacceptable.

## Decision

**Machine-readable registries and manifests are JSON.** Human-readable views are Markdown, generated from and
cross-referenced to the JSON.

Specifically:

1. `docs/data/source-registry.json` and `docs/data/licence-manifest.json` are the authoritative records.
2. Both are validated against JSON Schema under `schemas/data/` on every check.
3. `docs/data/attribution/ATTRIBUTIONS.md` and `docs/data/README.md` are human-readable views.
4. Dataset manifests under `datasets/manifests/` are JSON.
5. JSON is parsed with stdlib `json` only.
6. Every record carries an explicit `verification_status`. There is no default status; a missing status is a
   validation error.

## Rationale

1. **Validatable with stdlib.** The gate can actually be enforced in any environment.
2. **No implicit coercion.** JSON has no surprising type rules. A string is a string.
3. **Unambiguous.** One parse, one result. No anchors, no aliases, no duplicate-key ambiguity.
4. **Universally readable.** Every language, every tool, every diff viewer.
5. **Schema-native.** JSON Schema is designed for JSON.
6. **Honest about the constraint.** Choosing YAML would have meant shipping a registry that could not be
   validated in the environment where it is built.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **YAML** | Requires a third-party parser (prohibited by ADR-0002); not installable in the reference environment; implicit type coercion is unacceptable for a compliance-bearing file. |
| **TOML** | Stdlib support only from Python 3.11 (`tomllib`, read-only). Writing requires a third-party library. Poorly suited to nested arrays of records. |
| **A SQLite table** | The registry must be reviewable in a pull request diff. A binary database file is not. |
| **Markdown tables only** | Not reliably machine-parseable. The gate needs structure. |
| **JSON with a YAML front-matter variant** | Adds a parser requirement for no benefit. |

A future ADR may adopt YAML **in addition** to JSON, as a generated view, once a parser is available and an ADR
justifies the dependency. The JSON remains authoritative.

## Consequences

### Positive

- The licence gate is enforceable everywhere.
- Registry changes are reviewable in diffs.
- No implicit type coercion in a compliance-bearing file.
- Schema validation runs in CI and locally with no install step.

### Negative

- JSON is less pleasant to hand-edit than YAML: no comments, more punctuation.
- No inline comments. Mitigated: each record carries `_comment`-style descriptive fields where useful, and the
  Markdown views carry the prose.

### Neutral

- Contributors must edit JSON carefully. Mitigated: `make check-licences` fails loudly on malformed input.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/050-data-licensing.md` | §8 machine-readable records |
| `docs/architecture/BKB-CORPUS-001-corpus-ingestion.md` | §12 dataset manifest |
| `docs/data/README.md` | Authoritative record statement |
| `schemas/data/*.schema.json` | Validation |

## Verification

| Check | Command |
|---|---|
| Registry and manifest parse as JSON | `make check-licences` |
| Schema conformance | `python -m unittest tests.test_schemas` |
| Registry ↔ manifest consistency | `make check-licences` |
| Gate reads the manifest | `python -m unittest tests.test_licensing` |

## Related

ADR-0002, ADR-0010, BKB-CORPUS-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
