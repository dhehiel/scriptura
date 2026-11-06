# Documentation Index

All Scriptura documentation.

---

## Start here

| If you want to... | Read |
|---|---|
| Understand what Scriptura is | [../README.md](../README.md) |
| Contribute | [../CONTRIBUTING.md](../CONTRIBUTING.md) |
| Work on this repository as an AI agent | [../AGENTS.md](../AGENTS.md) — **binding** |
| Understand the rules that bind everyone | [../.clinerules/README.md](../.clinerules/README.md) |
| Understand the architecture | [architecture/README.md](architecture/README.md) |
| Propose a dataset | [data/README.md](data/README.md) and the dataset issue template |
| Understand the milestone position | [milestones/README.md](milestones/README.md) |
| Report a security or integrity problem | [../SECURITY.md](../SECURITY.md) — **not a public issue** |

---

## Architecture — normative

| Document | Governs |
|---|---|
| [architecture/README.md](architecture/README.md) | Specification index, identifier convention, change control, standing constraints |
| [architecture/BKB-ARCH-001-system-architecture.md](architecture/BKB-ARCH-001-system-architecture.md) | System decomposition, process model, module boundaries, deployment, Gomine interoperability |
| [architecture/BKB-DATA-001-data-model.md](architecture/BKB-DATA-001-data-model.md) | The seven epistemic layers, references, provenance, relational schema, invariants |
| [architecture/BKB-CORPUS-001-corpus-ingestion.md](architecture/BKB-CORPUS-001-corpus-ingestion.md) | Dataset lifecycle, licence gate, adapter contract, validation, provenance capture |
| [architecture/BKB-AGENTS-001-agent-framework.md](architecture/BKB-AGENTS-001-agent-framework.md) | Agent contracts, capability boundaries, evidence obligations, human review |
| [architecture/BKB-VERIFY-001-verification-framework.md](architecture/BKB-VERIFY-001-verification-framework.md) | Verification states, evidence chains, confidence, disagreement, assertion rules |
| [architecture/DKF-ARCH-001-discovery-framework.md](architecture/DKF-ARCH-001-discovery-framework.md) | Hypothesis lifecycle, discovery strategies, cross-domain linking, discovery integrity |
| [architecture/ADR/README.md](architecture/ADR/README.md) | Architecture Decision Records — ADR-0001 … ADR-0010 |

**Where a specification and an implementation disagree, the specification is authoritative and the
implementation is a bug.**

---

## Data governance

| Document | Purpose |
|---|---|
| [data/README.md](data/README.md) | Dataset governance policy; the two-tier licence model; verification status vocabulary |
| [data/source-registry.json](data/source-registry.json) | Dataset source registry (machine-readable, authoritative) |
| [data/licence-manifest.json](data/licence-manifest.json) | Licence manifest (machine-readable, authoritative; drives the gate) |
| [data/attribution/ATTRIBUTIONS.md](data/attribution/ATTRIBUTIONS.md) | Verbatim attribution strings required by upstream licences |

---

## Milestones

| Document | Purpose |
|---|---|
| [milestones/README.md](milestones/README.md) | Current milestone position and gating rules |
| [milestones/ROADMAP.md](milestones/ROADMAP.md) | The M0–M5 plan with scope and gating conditions |
| [milestones/M0-acceptance-criteria.md](milestones/M0-acceptance-criteria.md) | M0 exit criteria with per-criterion evidence |

---

## Research

| Document | Purpose |
|---|---|
| [research/README.md](research/README.md) | Research documentation index |
| [research/methodology.md](research/methodology.md) | Research methodology and standards |

---

## Operations

| Document | Purpose |
|---|---|
| [operations/README.md](operations/README.md) | Build, verification, database, and deployment operations |

---

## Schemas

| Document | Purpose |
|---|---|
| [../schemas/README.md](../schemas/README.md) | JSON Schema index and the supported validator subset |

---

## Governance

| Document | Purpose |
|---|---|
| [../GOVERNANCE.md](../GOVERNANCE.md) | Decision rights, specification change control, roles |
| [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Community standards |
| [../CHANGELOG.md](../CHANGELOG.md) | Release and milestone history |
| [../.clinerules/](../.clinerules/README.md) | Persistent project rules |

---

## Documentation standards

1. Markdown, GitHub-flavoured. Prose wrapped near 100 columns.
2. Every document has a title and a one-line purpose statement. Specifications add a status line.
3. Relative links for in-repository targets. `make check-docs` validates that every relative link resolves.
4. **Never state a licence, an availability, or a citation without a source.** Documentation is subject to the
   same source-integrity rules as code.
5. Specifications carry an ID, a status, and a change history.
6. Documentation is delivered **with** the change, not after it.

See [../.clinerules/040-engineering.md](../.clinerules/040-engineering.md) §7.
