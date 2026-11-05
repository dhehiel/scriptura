# ADR-0004 — FastAPI adoption gate

| Field | Value |
|---|---|
| **ID** | ADR-0004 |
| **Status** | Accepted |
| **Date** | M0 |
| **Deciders** | Maintainer |
| **Affects** | BKB-ARCH-001 §8.2; src/scriptura/api/ |
| **Supersedes** | — |

## Context

The task brief specifies "FastAPI when justified". That phrasing is itself the design instruction: FastAPI is a
candidate, not a default, and adoption requires justification.

At M0 the HTTP requirement is minimal: a read-only surface over a local SQLite file, bound to loopback, serving
JSON to a researcher's own tooling. There is no authentication requirement, no multi-tenancy, no concurrent
write load, no OpenAPI consumer, and no deployed service.

Adopting FastAPI would add a mandatory dependency chain (FastAPI, Starlette, Pydantic, an ASGI server) in
exchange for capabilities M0 does not use. Under ADR-0002 that chain cannot even be installed in the reference
environment, so the code paths could not be verified.

The Python standard library provides `http.server`, which is sufficient for a read-only local surface.

## Decision

**FastAPI is not adopted at M0.** The baseline HTTP surface is implemented with stdlib `http.server`.

FastAPI may be adopted later, **only** behind an accepted ADR that demonstrates all of the following:

1. A concrete requirement that stdlib `http.server` cannot satisfy.
2. Why that requirement cannot be met by extending the stdlib surface.
3. Licence compatibility of FastAPI and its full transitive dependency chain with Apache 2.0.
4. A supply-chain assessment of that chain.
5. A removal path, should the dependency need to be dropped.
6. That the surface remains **read-only** unless a separate ADR widens it.
7. That authentication and authorisation are specified if the surface is exposed beyond loopback.

Additionally:

- `src/scriptura/api/fastapi_app.py` exists as an **import-guarded, non-default** module. It raises a clear,
  actionable error when FastAPI is absent. It is never imported by default.
- The stdlib surface and the optional FastAPI surface expose the **same** read-only contract.
- Neither surface may expose a write endpoint without a separate accepted ADR.

## Rationale

1. **The requirement does not exist yet.** Adopting a framework for capabilities that are unused is cost without
   benefit.
2. **ADR-0002 compliance.** A mandatory dependency chain would violate the stdlib-only rule.
3. **Verifiability.** An uninstallable framework means unverifiable code paths.
4. **Attack surface.** A framework brings routing, deserialisation, and middleware behaviour that must be
   reasoned about for no current gain.
5. **Reversibility.** Deferring is cheap; removing an adopted framework later is expensive.
6. **The brief asked for justification.** This ADR is the record of what justification would look like.

## Alternatives considered

| Alternative | Why it was not chosen |
|---|---|
| **Adopt FastAPI now** | No requirement justifies it; violates ADR-0002; not installable in the reference environment. |
| **Adopt Flask** | Same objection: a dependency for an unused capability. |
| **No HTTP surface at all** | Rejected. A read-only local surface is genuinely useful for researcher tooling and notebooks, and is cheap with stdlib. |
| **stdlib surface, with FastAPI importable but unguarded** | Rejected. An unguarded optional import breaks at import time when absent, violating ADR-0002 §2. |
| **Wait and decide nothing** | Rejected. An undecided question gets re-litigated; this ADR records the gate so it does not. |

## Consequences

### Positive

- No dependency chain for an unused capability.
- The HTTP surface is small enough to audit completely.
- Read-only and loopback-only by default: minimal exposure.
- The adoption criteria are recorded, so the question is not re-litigated informally.

### Negative

- No automatic OpenAPI schema generation at M0.
- stdlib `http.server` is not designed for high concurrency. Accepted: the surface is local and low-volume.
- Contributors expecting FastAPI must read this ADR.

### Neutral

- `src/scriptura/api/fastapi_app.py` is present but inert without FastAPI installed.

## Compliance

| Document | Effect |
|---|---|
| `.clinerules/040-engineering.md` | §1 baseline table; FastAPI not adopted |
| `docs/architecture/BKB-ARCH-001-system-architecture.md` | §8.2 HTTP surface |
| `NOTICE` | §3 lists FastAPI as optional |
| `tests/test_api.py` | Enforces read-only and loopback default |
| `tests/test_dependency_hygiene.py` | Enforces no mandatory dependency |

## Verification

| Check | Command |
|---|---|
| stdlib surface is read-only | `python -m unittest tests.test_api` |
| Default bind is loopback | `python -m unittest tests.test_api` |
| FastAPI absent does not break import | `python -m unittest tests.test_api` |
| No mandatory dependency | `python -m unittest tests.test_dependency_hygiene` |

## Related

ADR-0002, BKB-ARCH-001

## Change history

| Date | Change |
|---|---|
| M0 | Initial. Accepted. |
