# Contributing to Scriptura

Thank you for your interest in Scriptura. This project is held to research standards rather than product
standards, and that shapes how contributions are reviewed. A contribution that adds capability at the cost of
provenance will be declined, however useful the capability looks.

Please read [AGENTS.md](AGENTS.md) and [.clinerules/](.clinerules/README.md) first. Human contributors and AI
agents are bound by the same substantive rules.

---

## Quick start

```bash
git clone https://github.com/dhehiel/scriptura.git
cd scriptura
export PYTHONPATH=src

# Verify the repository is healthy on your machine
make check
make test
```

No third-party packages are required for either command. Python 3.11+ and a SQLite build with FTS5 and JSON1
are the only prerequisites.

Optional development extras are declared in `pyproject.toml`:

```bash
pip install -e ".[dev]"     # pytest, ruff, mypy — optional; stdlib unittest works without them
```

---

## Ways to contribute

| Contribution | Where | Notes |
|---|---|---|
| Report a bug | [Issue](https://github.com/dhehiel/scriptura/issues) using the bug template | Include the failing check output |
| Fix a bug | Pull request | Requires a regression test |
| Improve documentation | Pull request | Run `make check-docs` |
| Propose a dataset | Issue using the dataset template | **Licence evidence is mandatory.** See below |
| Propose an architecture change | Issue using the ADR template | Must be accepted as an ADR before code |
| Add a language or canon profile | Pull request | Requires references + tests |
| Security or data-integrity report | See [SECURITY.md](SECURITY.md) | **Never a public issue** |

---

## Proposing a dataset

Dataset proposals are the most consequential contributions to this project, because a licensing error here
creates legal exposure for every downstream user. The bar is deliberately high.

A dataset proposal **must** include:

1. **Name and edition.** Exactly which edition, version, or release. "The Greek NT" is not a dataset.
2. **Rights holder.** Who owns the rights, as stated by the rights holder.
3. **Licence, exactly as written.** Name and version (e.g. `CC BY 4.0`, `CC BY-SA 4.0`, `CC BY-NC 4.0`,
   `CC0`, `public domain`, `MIT`, `Apache-2.0`). Or an explicit statement that the material is
   all-rights-reserved.
4. **Primary source URL.** The rights holder's own licence page — not an aggregator, not a mirror, not a
   forum post, not a model's recollection.
5. **Retrieval date.** When you actually read it.
6. **Verbatim attribution string**, if the licence requires specific wording.
7. **Derivative and commercial status.** Whether derivatives are permitted, and whether commercial use is.
8. **Share-alike status.** If the licence is share-alike, say so — it constrains what Scriptura may do with
   derived data.
9. **Jurisdiction notes.** Particularly for public-domain claims. Some texts are public domain in most
   jurisdictions but not in all.

**Proposals without licence evidence will be closed.** A proposal that says "this should be freely available"
is not evidence. If you cannot find the licence, say so — an honest `unverified` entry is valuable; a guessed
licence is harmful.

Two facts contributors routinely get wrong, and which reviewers will check:

- **Aggregator-level licences do not establish item-level rights.** Several major aggregators license
  per item and state that there is no overall licence for the collection. Citing the platform's terms does
  not establish rights for any specific text.
- **A collection licence does not cover annotations, and an annotation licence does not cover the text.**
  Composite datasets are frequently licensed in layers, with the underlying text under one licence and the
  added analysis under another. Both must be resolved.

See [.clinerules/050-data-licensing.md](.clinerules/050-data-licensing.md) and
[docs/data/README.md](docs/data/README.md).

---

## Code standards

### Language and dependencies

- Python 3.11+. Type hints on all public functions.
- **Zero mandatory third-party runtime dependencies.** Stdlib only. This is enforced by
  `tests/test_dependency_hygiene.py`.
- Optional integrations (`leann`, `fastapi`) must be import-guarded, detected via a capability probe, and
  degrade gracefully. A missing optional dependency must never raise at import time.

### Style

- Follow the existing module layout under `src/scriptura/`.
- `ruff` and `mypy` configurations are in `pyproject.toml`. They are advisory at M0 and will become gating.
- Docstrings on public API. Reference the governing specification where one applies.
- No new conventions in drive-by changes. If a convention should change, propose it separately.

### Structure

- One concern per module. Do not create catch-all utility modules.
- Public API is whatever is exported from a package `__init__.py`.
- Errors derive from `scriptura.core.errors.ScripturaError`. Do not raise bare `Exception`.

### Data and schema

- Every schema change updates the corresponding JSON Schema under `schemas/`.
- Migrations live in `src/scriptura/storage/migrations/` and are **additive and forward-only**. Never edit an
  applied migration; add a new one with a higher sequence number.
- Every persisted record that makes a claim carries an epistemic layer. No exceptions.

---

## Testing requirements

- **Every behaviour change requires a test.** No exceptions at review time.
- Tests must run under stdlib `unittest` **and** under `pytest`. Do not use pytest-only fixtures in a way that
  breaks `python -m unittest discover`.
- Tests must not require network access. Network-dependent tests must be skipped, not failed, when offline.
- Tests must not write outside a temporary directory. Use `tempfile`.
- Negative tests are required for every validator: what it must reject is as important as what it accepts.

Run:

```bash
make test           # stdlib unittest discovery
make check          # repository, hygiene, licence, link, and schema checks
```

Both must pass before a PR is considered ready.

---

## Documentation standards

- Markdown, GitHub-flavoured. Wrap prose at roughly 100 columns.
- Every document has a title, a one-line purpose statement, and a status line where it is a specification.
- Relative links for in-repository targets. `make check-docs` validates that every relative link resolves.
- Specifications carry an ID (e.g. `BKB-DATA-001`), a status, and a change history.
- **Never state a licence, an availability, or a citation without a source.** Documentation is subject to the
  same source-integrity rules as code.

---

## Pull request process

1. Open an issue first for anything non-trivial. Architecture changes need an accepted ADR before code.
2. Branch from `main`. Keep the change focused; split unrelated changes.
3. Write or update tests.
4. Update documentation affected by the change.
5. Run `make check` and `make test`. Paste the output into the PR description if either is slow to reproduce.
6. Complete the PR template, including the compliance checklist.
7. Request review.

### Review requirements

| Change type | Requires |
|---|---|
| Documentation only | 1 review |
| Code, no schema change | 1 review + passing CI |
| Schema or migration change | 1 review + maintainer approval |
| Architecture specification change | Accepted ADR + maintainer approval |
| Dataset or licence change | Maintainer approval + primary-source licence evidence |
| Anything touching provenance | Maintainer approval |

Reviewers will specifically check: provenance completeness, layer correctness, licence accuracy, absence of
fabricated citations, absence of new mandatory dependencies, and absence of new services.

---

## What will get a contribution declined

- Fabricated or unverifiable citations, identifiers, or licence claims.
- Unattributed theological interpretation presented as fact.
- Model-generated text presented as scripture.
- AI-generated inference presented without the `ai_hypothesis` flag.
- A new mandatory runtime dependency without an accepted ADR.
- A microservice, message broker, or separate graph database without an accepted ADR.
- Committed corpus data.
- A licence upgrade relative to what the primary source states.
- Work reported as complete that was not performed and verified.

---

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Scriptura handles material that communities hold sacred, and contributors will disagree deeply about canon,
translation, and doctrine. That disagreement is expected and is not a conduct problem. Treating a person badly
because of their position is.

The project records disagreement in data rather than resolving it by argument.

---

## Licensing your contribution

By submitting a contribution you agree that it is provided under the
[Apache License, Version 2.0](LICENSE) and that you are entitled to license it on those terms.

This applies to **your code and documentation**. It does not apply to third-party corpus data, which is
governed per dataset by its own rights holder and is never relicensed by contributing to this repository.

---

## Getting help

Open an issue with your question. There are no bad questions here, and "I could not find the licence for X" is
a genuinely useful contribution.
