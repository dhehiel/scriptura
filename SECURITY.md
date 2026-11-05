# Security and Integrity Policy

Scriptura is a research data project. Its threat model is unusual: alongside conventional software security
concerns, the most severe risks are **data-integrity risks** — fabricated provenance, corrupted text, misapplied
licences, and silently collapsed epistemic layers. All four are treated as security incidents here, because all
four damage every downstream consumer and are difficult to detect after the fact.

---

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Use one of these channels:

1. **GitHub private vulnerability reporting** — preferred. Enable and use the "Report a vulnerability" option
   under the *Security* tab of https://github.com/dhehiel/scriptura.
2. **Direct contact with the maintainers** — if private reporting is unavailable, contact the repository owner
   through the contact details published on their GitHub profile, with `[SCRIPTURA-SECURITY]` in the subject.

### What to include

- A description of the issue and its impact.
- Steps to reproduce, or a proof of concept. Minimal is fine.
- Affected version, commit, or milestone.
- Whether the issue is already public.

### What we commit to

| Item | Commitment |
|---|---|
| Acknowledgement | Within **72 hours** of receipt |
| Initial assessment | Within **7 days** |
| Updates | Every **7 days** while an issue is open |
| Fix or mitigation | Targeted at **30 days** for confirmed high-severity issues |
| Credit | Reporters are credited in the advisory unless they ask not to be |
| Retaliation | None. Good-faith reporters are never treated adversarially |

We ask for reasonable notice before public disclosure, and we will not ask you to delay disclosure indefinitely.

---

## Scope

### In scope

- Code execution, injection, or path traversal in `src/scriptura/` or `tools/`.
- Unsafe deserialisation, unsafe file handling, or unsafe subprocess use.
- The HTTP surface (`src/scriptura/api/`) — including any path that allows writes, since the surface is
  specified as read-only.
- SQLite misuse that permits corruption, unbounded resource use, or leakage across a boundary.
- Licence manifest or source registry tampering, including any path that lets an `unverified` dataset be
  ingested.
- Provenance tampering: any path that permits silent mutation or deletion of provenance records.
- Epistemic layer bypass: any path that permits unflagged `ai_hypothesis` output, unattributed
  `theological_interpretation`, or promotion of content between layers.
- Supply-chain issues: introduction of an undeclared dependency, or a dependency whose licence is incompatible
  with Apache 2.0.

### Out of scope

- Reports requiring physical access to a machine already compromised.
- Denial-of-service against a self-hosted instance operated by the reporter.
- Findings in optional third-party components (for example LEANN or FastAPI) that are not caused by Scriptura's
  use of them. Please report those upstream; we will track and pin the fix.
- Social engineering of maintainers.

---

## Severity model

Scriptura uses a four-level model. Note that **data-integrity severity is assessed independently of code
severity**; a provenance defect can be Critical without any memory-safety or execution component.

| Severity | Definition | Examples |
|---|---|---|
| **Critical** | Fabricated or forgeable provenance; licence gate bypass permitting unlicensed data; layer bypass permitting unflagged AI output as authoritative; remote code execution | Ingestion proceeds despite `verification_status: unverified`; `ai_hypothesis` emitted without the flag; provenance rows silently mutable |
| **High** | Silent text corruption; cross-dataset identifier collision; write access via the read-only API; injection | A record's text differs from its recorded source hash; two datasets share a namespace and collide |
| **Medium** | Integrity weakness with limited blast radius; missing validation that a reviewer would catch | A validator accepts malformed input that a schema should reject |
| **Low** | Hygiene and hardening | Missing input length limits; verbose error output |

---

## Data-integrity incidents

These are reportable through the same channel and are treated with the same urgency as code vulnerabilities.

Report immediately if you find:

- **Corpus data committed to the repository.** No dataset bytes belong in version control.
- **A licence recorded more permissively than the primary source states.** This is a compliance defect with
  downstream legal consequences.
- **An attribution requirement not reproduced verbatim** where the licence mandates specific wording.
- **Share-alike obligations not propagated** to derived datasets.
- **A fabricated or unresolvable citation, identifier, DOI, or manuscript siglum** anywhere in the repository,
  including in documentation.
- **Text whose content does not match its recorded provenance hash.**
- **An epistemic layer missing, defaulted, or silently inferred** on a persisted claim.
- **Scripture text that was generated rather than sourced.**

When such an issue is confirmed we will, in order:

1. **Stop the bleed.** Disable or revert the affected path.
2. **Identify the blast radius.** Which records, datasets, and derived artefacts are affected.
3. **Preserve the audit trail.** Provenance is append-only; we do not quietly delete evidence of the defect.
4. **Notify downstream consumers** through a security advisory and a `CHANGELOG.md` entry.
5. **Add a regression test** that would have caught it, and a `make check` rule where one is expressible.

---

## Security posture at M0

The current design reduces attack surface deliberately:

| Property | Status |
|---|---|
| Mandatory third-party runtime dependencies | **None.** Stdlib only. |
| Network access required at runtime | **None.** |
| Corpus data present | **None.** |
| Autonomous agents | **None implemented.** |
| Microservices | **None.** Single process. |
| Default HTTP surface | Read-only, stdlib, bind-local by default, not enabled unless explicitly started |
| Database | Local SQLite file; no server, no listening socket, no authentication surface |
| Deserialisation | JSON only, via stdlib `json`. No pickle, no `eval`, no `exec`, no dynamic import of data |

These properties are checked by `make check`. Regressions fail CI.

### Rules that maintain the posture

- Do not add a mandatory third-party dependency without an accepted ADR.
- Do not add network I/O to the runtime path. Retrieval is a separate, human-invoked ingestion step.
- Do not introduce `pickle`, `eval`, `exec`, `marshal`, or dynamic code generation.
- Do not widen the HTTP surface beyond read-only without an accepted ADR.
- Do not bind to a non-loopback interface by default.
- Do not log or persist secrets. Scriptura has no legitimate need for credentials.

---

## Dependency and supply-chain policy

- Mandatory dependencies require an accepted ADR covering necessity, licence compatibility with Apache 2.0,
  maintenance status, and a removal path.
- Optional dependencies are import-guarded and must not affect correctness when absent.
- Pinned versions for anything used in CI.
- No dependency may be added whose licence is incompatible with Apache 2.0 without explicit legal review.
- Corpus data is never treated as a software dependency and never enters `pyproject.toml`.

---

## Disclosure policy

- We coordinate disclosure with reporters and aim to publish an advisory alongside a fix.
- Confirmed issues are recorded in [CHANGELOG.md](CHANGELOG.md).
- We credit reporters unless they decline.
- We do not pursue legal action against good-faith researchers.

---

## Related documents

- [AGENTS.md](AGENTS.md) — binding agent obligations, including anti-fabrication rules
- [.clinerules/010-source-integrity.md](.clinerules/010-source-integrity.md) — source integrity rules
- [.clinerules/050-data-licensing.md](.clinerules/050-data-licensing.md) — licence compliance rules
- [.clinerules/060-agent-safety.md](.clinerules/060-agent-safety.md) — autonomy boundaries
- [BKB-VERIFY-001](docs/architecture/BKB-VERIFY-001-verification-framework.md) — verification framework
