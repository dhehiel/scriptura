# DKF-ARCH-001 — Discovery and Knowledge Framework

**Discovery and Knowledge Framework — Architecture**

| Field | Value |
|---|---|
| **ID** | DKF-ARCH-001 |
| **Status** | Accepted |
| **Version** | 1.0.0 |
| **Milestone** | M0 |
| **Owner** | Maintainer |
| **Normative** | Yes |
| **Supersedes** | — |

## Abstract

This specification defines how Scriptura generates, ranks, tracks, and disposes of research hypotheses: the
hypothesis lifecycle, discovery strategies, cross-domain linking, salience ranking, the discovery output
contract, and the integrity rules that prevent a generated pattern from acquiring the standing of a finding. It
establishes that discovery in Scriptura produces **candidates for human investigation**, never conclusions.

---

## 1. Purpose and scope

### 1.1 Purpose

Discovery is where a knowledge base earns its name. A store that can only return what was explicitly put into it
is an index. Scriptura's discovery layer finds relationships that no single source asserted — lexical echoes,
structural parallels, cross-domain correspondences — and surfaces them for investigation.

Discovery is also where a knowledge base is most dangerous. A pattern found by a model is not a finding, and a
system that presents it as one manufactures false authority at scale. This specification exists to make that
failure structurally impossible.

### 1.2 In scope

Hypothesis lifecycle; discovery strategies; cross-domain linking; salience ranking; the discovery output
contract; discovery integrity; evaluation.

### 1.3 Out of scope

Verification semantics ([BKB-VERIFY-001](BKB-VERIFY-001-verification-framework.md)); agent contracts
([BKB-AGENTS-001](BKB-AGENTS-001-agent-framework.md)); the layer model
([BKB-DATA-001](BKB-DATA-001-data-model.md)); graph storage ([BKB-DATA-001 §6](BKB-DATA-001-data-model.md)).

---

## 2. Core principle

> **Discovery produces candidates for human investigation. It never produces conclusions.**

Every discovery output is an `ai_hypothesis` record unless a cited source establishes a stronger warrant. It is
flagged non-authoritative at every presentation boundary. It may not be promoted by relabelling.

Corollary: **the value of a discovery is measured by the investigation it prompts, not by the confidence it
projects.**

---

## 3. Hypothesis lifecycle

### 3.1 States

```
                 ┌───────────┐
   strategy ────▶│ generated │
                 └─────┬─────┘
                       │ deduplicated, ranked
                       ▼
                 ┌───────────┐   dismissed   ┌────────────┐
                 │ candidate │──────────────▶│ dismissed  │
                 └─────┬─────┘               └────────────┘
                       │ selected for investigation
                       ▼
                ┌──────────────┐
                │ investigating│
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┬─────────────────┐
        ▼              ▼              ▼                 ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐   ┌────────────┐
  │ supported │  │ contested │  │  refuted  │   │ inconclusive│
  └───────────┘  └───────────┘  └───────────┘   └────────────┘
```

### 3.2 State semantics

| State | Meaning | Layer | Who may set it |
|---|---|---|---|
| `generated` | Produced by a strategy; not yet examined | `ai_hypothesis` | The strategy |
| `candidate` | Deduplicated, ranked, awaiting selection | `ai_hypothesis` | The framework |
| `investigating` | Selected for human investigation | `ai_hypothesis` | A human |
| `supported` | Evidence chain supports it | **The layer the evidence warrants** | A human, via verification |
| `contested` | Evidence points in different directions | As warranted | A human, via verification |
| `refuted` | Evidence contradicts it | As warranted | A human, via verification |
| `inconclusive` | Investigation did not resolve it | `ai_hypothesis` | A human |
| `dismissed` | Judged not worth investigating | `ai_hypothesis` | A human |

### 3.3 Lifecycle rules

| # | Rule |
|---|---|
| HL1 | Every hypothesis begins at `generated`, in the `ai_hypothesis` layer |
| HL2 | No strategy may emit a hypothesis in any other layer |
| HL3 | A transition out of `ai_hypothesis` requires an evidence chain and a human decision, recorded |
| HL4 | `supported`, `contested`, and `refuted` are set by **verification**, per BKB-VERIFY-001 — not by the discovery framework |
| HL5 | `refuted` and `dismissed` hypotheses are **retained**. They are never deleted |
| HL6 | A refuted hypothesis is retained with its refutation, so the same pattern is not re-proposed |
| HL7 | Every transition is recorded with actor and timestamp |
| HL8 | A hypothesis may not skip states |
| HL9 | `inconclusive` is a legitimate terminal state. It is not a failure |

### 3.4 Why refuted and dismissed hypotheses are retained

Discovery strategies are re-run. Without retention, the same false pattern is re-proposed indefinitely and
re-reviewed indefinitely. A retained refutation is a **negative result**, which is a real result. See
[.clinerules/030-research-standards.md](../../.clinerules/030-research-standards.md) §6.

---

## 4. Discovery strategies

### 4.1 Strategy contract

A strategy is a deterministic or seeded-stochastic function over the knowledge base that emits hypotheses.

| # | Requirement |
|---|---|
| ST1 | Declares its identity and version |
| ST2 | Declares the layers it reads |
| ST3 | Emits only `ai_hypothesis` records |
| ST4 | Emits, for each hypothesis: the pattern, the inputs, the method, a confidence, and a **falsification condition** |
| ST5 | Is deterministic, or records its seed |
| ST6 | Does not mutate the knowledge base |
| ST7 | Does not resolve disagreement |
| ST8 | Does not promote layers |
| ST9 | Records what it searched and what it did not find |
| ST10 | Operates on a bounded scope |

### 4.2 Baseline strategy families

| Family | What it looks for | Example |
|---|---|---|
| **Lexical echo** | Shared lemma, form, or rare phrase across passages | A hapax echoed in a later text |
| **Structural parallel** | Parallel syntax, chiasm, inclusio, formulaic patterns | A shared covenant formula |
| **Intertextual candidate** | Quotation, allusion, or echo between texts | A Pauline allusion to a LXX reading |
| **Version divergence** | Where translations or witnesses diverge systematically | A consistent rendering choice in a version |
| **Semantic field** | Words clustering in a semantic domain | A term's distribution across a corpus |
| **Cross-domain correspondence** | Scripture ↔ external evidence ↔ linguistic data | An inscription bearing on a toponym |
| **Temporal clustering** | Dating evidence clustering around a text or event | A composition-date hypothesis |
| **Reception pattern** | How a passage is read across traditions | A passage's interpretive history |

Each family is a **search pattern**, not a claim. The output is "this pattern is present", never "this means
that".

### 4.3 Falsification conditions are mandatory

A hypothesis without a stated falsification condition is not a hypothesis; it is an observation dressed as one.
Every emitted hypothesis records what evidence **would** refute it. This makes the hypothesis investigable and
makes the eventual disposition meaningful.

---

## 5. Cross-domain linking

### 5.1 The domains

Discovery links across the seven epistemic layers. **A link's layer is assigned explicitly; it is NEVER
inherited from its endpoints** -- there is no weakest-layer computation (ADR-0011, rules D1-D2).

| Link situation | Link layer |
|---|---|
| Proposed by a discovery strategy | **Always `ai_hypothesis`**, whatever the endpoints are |
| An edition itself asserts the relation | `scripture`, citing the edition |
| A textual apparatus asserts the comparison | `textual_observation`, citing the apparatus |
| A dataset asserts the linguistic relation | `linguistic_observation`, citing the dataset |
| External evidence itself asserts the relation | `historical_evidence`, citing the evidence |
| A named scholar argues it in a named work | `scholarly_interpretation`, attributed |
| A named tradition holds it | `theological_interpretation`, attributed |
| Any endpoint is `ai_hypothesis` (unverified chain) | `ai_hypothesis` |

A link may only take a non-`ai_hypothesis` layer where **a source asserts the link itself**, not merely its
endpoints, and where the derivation record records the inputs, method, and actor.

### 5.2 Rules

| # | Rule |
|---|---|
| XL1 | A link proposed by a strategy is `ai_hypothesis`, regardless of its endpoints |
| XL2 | A link may only take a non-`ai_hypothesis` layer where a **source asserts the link**, and only with a derivation record preserving inputs, method, and actor |
| XL3 | Cross-layer linking must never imply that evidence inherits scriptural authority |
| XL4 | A link between `historical_evidence` and `scripture` never asserts that the evidence proves the scripture |
| XL5 | Links carry provenance and confidence |
| XL6 | Links are stored as graph edges and are subject to BKB-DATA-001 §6.5 |
| XL7 | A link is never presented without the layers of both endpoints |

Rule XL4 is the single most important integrity rule in this specification. Archaeology does not prove scripture,
and scripture does not authenticate archaeology. A system that implies otherwise is manufacturing apologetics
under the guise of data.

---

## 6. Salience ranking

### 6.1 Purpose

Discovery produces far more hypotheses than can be investigated. Ranking selects what a human sees first.

### 6.2 Ranking signals

| Signal | Direction |
|---|---|
| Rarity of the pattern | Rarer is more salient |
| Specificity of the match | More specific is more salient |
| Independence of supporting sources | More independent is more salient |
| Novelty — not previously proposed, supported, refuted, or dismissed | Novel is more salient |
| Breadth of layers involved | More layers is more salient, **but** never raises the link's layer |
| Falsifiability | A clearly falsifiable hypothesis is more salient |
| Previously refuted | **Suppressed.** Not re-proposed |
| Previously dismissed | Suppressed unless new evidence exists |

### 6.3 Ranking rules

| # | Rule |
|---|---|
| RK1 | Ranking affects **order**, never **layer** or **confidence** |
| RK2 | A high rank never raises a hypothesis's warrant |
| RK3 | Rank is recorded with the signals that produced it |
| RK4 | Ranking is reproducible: same inputs, same order |
| RK5 | A refuted or dismissed hypothesis is not re-ranked into view without new evidence |
| RK6 | Ranking never resolves disagreement |
| RK7 | Ranking must not be presented as a measure of truth |

---

## 7. Discovery output contract

Every discovery output conforms to the `ai_hypothesis` requirements of
[BKB-DATA-001 §2.2](BKB-DATA-001-data-model.md), plus:

| Field | Requirement |
|---|---|
| `strategy_id`, `strategy_version` | Mandatory |
| `pattern` | What was found, described precisely |
| `endpoints` | The records linked, by identifier, with their layers |
| `link_layer` | Mandatory — always `ai_hypothesis` at generation |
| `inputs` | Input identifiers |
| `method` | The method, or a hash of it |
| `model` | Where a model was involved |
| `confidence` | Mandatory, in `[0, 1]` |
| `falsification_condition` | **Mandatory** |
| `rank`, `rank_signals` | Where ranked |
| `lifecycle_state` | Mandatory |
| `non_authoritative` | **Mandatory, always `true` at generation** |
| `generated_at` | Mandatory |
| `negative_results` | What was searched and not found |

### 7.1 Presentation obligations

| # | Rule |
|---|---|
| PO1 | Every discovery output is flagged non-authoritative, and the flag is not removable by the consumer |
| PO2 | Both endpoint layers are shown alongside any link |
| PO3 | The falsification condition is shown alongside the hypothesis |
| PO4 | Confidence is shown with its basis |
| PO5 | Rank is never presented as a measure of truth |
| PO6 | A mixed-layer result set visibly distinguishes layers |
| PO7 | Discovery output is never presented as a finding, a conclusion, or a consensus |

---

## 8. Discovery integrity

| # | Rule |
|---|---|
| DI1 | Discovery never fabricates. A strategy that cannot find a pattern reports nothing |
| DI2 | Discovery never invents identifiers, sigla, references, or citations |
| DI3 | Discovery never generates text and presents it as sourced |
| DI4 | Discovery never promotes a layer |
| DI5 | Discovery never mutates provenance |
| DI6 | Discovery never resolves a doctrinal or canonical disagreement |
| DI7 | Discovery never treats majority as authority |
| DI8 | Discovery records negative results |
| DI9 | Discovery is reproducible, or records its seed |
| DI10 | Discovery operates on a bounded scope and reports the scope it covered |
| DI11 | Discovery never asserts authorial intent as fact |
| DI12 | Discovery never asserts that a pattern implies a historical fact |

---

## 9. Evaluation

Discovery quality is measured, not assumed.

| Metric | Definition |
|---|---|
| **Precision** | Proportion of proposed hypotheses judged worth investigating |
| **Novelty** | Proportion not previously proposed |
| **Falsifiability** | Proportion with a usable falsification condition |
| **Investigation yield** | Proportion of investigated hypotheses reaching a non-`inconclusive` disposition |
| **Refutation rate** | Proportion refuted — reported, not hidden |
| **Re-proposal rate** | Proportion re-proposed after refutation or dismissal — **must be near zero** |
| **Layer integrity** | Proportion of outputs correctly layered — **must be 100%** |
| **Flag integrity** | Proportion of outputs correctly flagged — **must be 100%** |

| # | Rule |
|---|---|
| EV1 | Evaluation datasets are versioned and provenanced, and carry their own licensing |
| EV2 | Per-case results are reported, not only aggregates |
| EV3 | Negative evaluation results are published |
| EV4 | A benchmark chosen because a strategy passes it is not an evaluation |
| EV5 | Layer integrity and flag integrity below 100% is a **blocking defect**, not a metric |
| EV6 | A high refutation rate is not a failure. A hidden one is |

---

## 10. Relationship to the knowledge graph

Discovery reads and proposes against the modular knowledge graph specified in
[BKB-DATA-001 §6](BKB-DATA-001-data-model.md). It is the primary consumer of graph traversal.

| # | Rule |
|---|---|
| KG1 | Discovery reads the graph; it never rewrites it |
| KG2 | Proposed links are new edges in the `ai_hypothesis` layer |
| KG3 | Traversal queries must be able to filter by layer, and discovery reports which layers it traversed |
| KG4 | Discovery never traverses in a way that silently merges layers |
| KG5 | Graph-based discovery is bounded by traversal depth and node count |
| KG6 | Discovery does not require a graph database. It operates on the SQLite graph model per
  [ADR-0005](ADR/ADR-0005-no-graph-database.md) |

---

## 11. Implementation status at M0

| Deliverable | Status |
|---|---|
| Hypothesis lifecycle | Specified |
| Strategy contract | Specified |
| Baseline strategy families | Specified |
| Cross-domain linking rules | Specified |
| Salience ranking | Specified |
| Output contract | Specified |
| Integrity rules | Specified |
| Evaluation metrics | Specified |
| Strategy implementations | **Not implemented** — no corpus exists to discover over |

Strategy implementation is scheduled for **M3**, when the graph is populated. See
[../milestones/ROADMAP.md](../milestones/ROADMAP.md).

---

## 12. Prohibitions

| # | Prohibition |
|---|---|
| P1 | Emitting a hypothesis in any layer other than `ai_hypothesis` |
| P2 | Emitting a hypothesis without a falsification condition |
| P3 | Emitting an unflagged discovery output |
| P4 | Promoting a hypothesis by relabelling |
| P5 | Deleting a refuted or dismissed hypothesis |
| P6 | Re-proposing a refuted hypothesis without new evidence |
| P7 | Presenting a pattern as a conclusion |
| P8 | Presenting rank as truth |
| P9 | Implying that external evidence proves scripture, or that scripture authenticates evidence |
| P10 | Resolving a doctrinal or canonical disagreement |
| P11 | Fabricating a pattern, identifier, or citation |
| P12 | Omitting negative results |
| P13 | Asserting authorial intent as fact |
| P14 | Reporting layer or flag integrity below 100% as an acceptable metric |

---

## 13. Verification of this specification

| Check | Command |
|---|---|
| Layer invariants enforced | `python -m unittest tests.test_layers` |
| Graph constraints, including layer typing | `python -m unittest tests.test_graph` |
| Layer-filtered traversal | `python -m unittest tests.test_graph` |
| `non_authoritative` enforced for `ai_hypothesis` | `python -m unittest tests.test_layers`, `tests.test_graph` |
| Full suite | `make test` |

---

## 14. Change history

| Version | Date | Change | ADR |
|---|---|---|---|
| 1.0.0 | M0 | Initial specification: hypothesis lifecycle, strategy contract, baseline strategy families, cross-domain linking, salience ranking, output contract, discovery integrity, evaluation. Strategy implementations deferred to M3. | ADR-0007, ADR-0008 |
