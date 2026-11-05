# Architecture Documentation

Normative architecture documentation for Scriptura.

---

## Foundational specifications

Six specifications define the system. All are **normative**: where a specification and an implementation
disagree, the specification is authoritative and the implementation is a bug.

| ID | Title | File | Status |
|---|---|---|---|
| **BKB-ARCH-001** | System Architecture | [BKB-ARCH-001-system-architecture.md](BKB-ARCH-001-system-architecture.md) | Accepted |
| **BKB-DATA-001** | Data Model and Epistemic Layers | [BKB-DATA-001-data-model.md](BKB-DATA-001-data-model.md) | Accepted |
| **BKB-CORPUS-001** | Corpus Ingestion | [BKB-CORPUS-001-corpus-ingestion.md](BKB-CORPUS-001-corpus-ingestion.md) | Accepted |
| **BKB-AGENTS-001** | Research Agent Framework | [BKB-AGENTS-001-agent-framework.md](BKB-AGENTS-001-agent-framework.md) | Accepted |
| **BKB-VERIFY-001** | Verification Framework | [BKB-VERIFY-001-verification-framework.md](BKB-VERIFY-001-verification-framework.md) | Accepted |
| **DKF-ARCH-001** | Discovery and Knowledge Framework | [DKF-ARCH-001-discovery-framework.md](DKF-ARCH-001-discovery-framework.md) | Accepted |

### Identifier convention

| Prefix | Domain |
|---|---|
| `BKB-` | Biblical Knowledge Base — the scripture, corpus, and knowledge substrate |
| `DKF-` | Discovery and Knowledge Framework — hypothesis generation and cross-domain discovery |

Format: `<PREFIX><DOMAIN>-<NNN>-<kebab-title>.md`. Numbers are sequential within a domain and **never reused**,
even for a retired specification.

### Specification statuses

| Status | Meaning |
|---|---|
| `draft` | Being written; not binding |
| `proposed` | Complete; awaiting decision |
| `accepted` | Binding |
| `superseded` | Replaced by a named later specification |
| `deprecated` | No longer applies; not replaced |

An accepted specification may be superseded **only** by another accepted specification. It is never silently
edited. Every specification carries a `Change history` section.

---

## How the specifications relate

```
                    BKB-ARCH-001  (system decomposition)
                          │
          ┌───────────────┼───────────────────┐
          ▼               ▼                   ▼
    BKB-DATA-001    BKB-CORPUS-001      BKB-AGENTS-001
    (what may be    (how data enters,   (who may act,
     stored, and     licence-gated)      and within what
     how typed)                          boundaries)
          │               │                   │
          └───────┬───────┴───────────────────┘
                  ▼
           BKB-VERIFY-001  (what may be asserted)
                  │
                  ▼
            DKF-ARCH-001   (what may be proposed)
```

- **BKB-ARCH-001** defines the container: modules, process model, boundaries, deployment, Gomine interop.
- **BKB-DATA-001** defines what may be stored and how it is typed. This is the load-bearing specification: the
  five epistemic layers originate here and every other specification depends on them.
- **BKB-CORPUS-001** defines how data enters, gated by licence verification.
- **BKB-AGENTS-001** defines who may act and within what boundaries. Specified at M0; **not implemented**.
- **BKB-VERIFY-001** defines what may be asserted, given evidence.
- **DKF-ARCH-001** defines what may be proposed, given the knowledge base.

---

## Architecture Decision Records

Decisions that constrain or extend the specifications are recorded in [ADR/](ADR/README.md).

An ADR is required for any decision that is hard to reverse, architecturally load-bearing, a relaxation of a
standing constraint, contested, or likely to be re-litigated. See
[.clinerules/070-decision-log-protocol.md](../../.clinerules/070-decision-log-protocol.md).

---

## Change control

Changing a specification is a governance act:

1. Open an issue stating the **problem**, not the preferred solution.
2. Draft an ADR with status `proposed`.
3. Discuss. Consult domain reviewers where the change touches scripture, language, history, theology, or
   licensing.
4. Maintainer sets `accepted`, `rejected`, or `deferred`, with reasons recorded.
5. On acceptance, revise the affected specification: update `Status` and `Change history`, reference the ADR.
6. Implementation **follows** the accepted specification. It never precedes it.

---

## Standing constraints

Consolidated from `.clinerules/` and the ADRs. Relaxing any requires an accepted ADR.

| # | Constraint | Source |
|---|---|---|
| 1 | No corpus ingestion before architecture review | BKB-CORPUS-001 §2 |
| 2 | No autonomous agents without explicit authorisation | BKB-AGENTS-001 §2 |
| 3 | No microservices, brokers, or worker pools | BKB-ARCH-001 §5.3 |
| 4 | No independent graph database | ADR-0005 |
| 5 | No mandatory third-party runtime dependency | ADR-0002 |
| 6 | FastAPI adoption is gated | ADR-0004 |
| 7 | No unlicensed or unverified dataset | ADR-0010 |
| 8 | No collapse of epistemic layers | BKB-DATA-001 §2 |
| 9 | No runtime dependency on Gomine | BKB-ARCH-001 §10 |
| 10 | No runtime network I/O | BKB-ARCH-001 §11 |

Each is checked by `make check` or `make test`.
