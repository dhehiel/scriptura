"""The seven epistemic layers.

Normative source: BKB-DATA-001 section 2; ADR-0011 (supersedes ADR-0008);
.clinerules/020-epistemic-layers.md.

Scriptura's foundational architectural commitment. The layer set is CLOSED:
adding a layer requires an accepted ADR.

**Layers classify the NATURE of a knowledge record. They are not levels of
truth, reliability, or authority, and there is NO ranking among them.** The
universal ranking previously provided here (`LAYER_ORDER`, `layer_strength`,
`weakest_layer`, `compose_layer`) was removed by ADR-0011 and must not be
reintroduced under another name. Confidence, evidence quality, provenance,
verification status, disagreement, tradition, and attribution are independent
metadata dimensions and never determine a layer.

This module enforces the layer invariants at the type level. The same
invariants are enforced again by SQL CHECK constraints (migration
`0001_bootstrap.sql` plus `0002_seven_layer_epistemic_model.sql`), because a
constraint that lives only in application code can be bypassed by a future code
path, a script, or a direct SQL client.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .errors import DerivationError, LayerValidationError, PromotionError

__all__ = [
    "EpistemicLayer",
    "LAYER_VALUES",
    "NON_AUTHORITATIVE_LAYER",
    "LayerRequirement",
    "LAYER_REQUIREMENTS",
    "DerivationRecord",
    "CONDITIONS",
    "coerce_layer",
    "is_valid_layer",
    "validate_layer_fields",
    "require_flag",
    "serialise_layer_metadata",
    "assert_not_promotion",
    "validate_derivation",
]


class EpistemicLayer(str, Enum):
    """The closed set of seven epistemic layers (ADR-0011).

    Subclasses :class:`str` so that a layer can be compared directly against the
    string values used in SQL CHECK constraints and JSON serialisation, without
    losing enum safety at the Python boundary.
    """

    #: Text as attested by a named edition, translation, or manuscript witness.
    SCRIPTURE = "scripture"

    #: Manuscript readings, textual variants, transmission phenomena, textual
    #: criticism, witness comparisons.
    TEXTUAL_OBSERVATION = "textual_observation"

    #: Morphology, syntax, lexicography, semantics, phonology, orthography,
    #: discourse analysis.
    LINGUISTIC_OBSERVATION = "linguistic_observation"

    #: Archaeological, documentary, inscriptional, material evidence external
    #: to scripture.
    HISTORICAL_EVIDENCE = "historical_evidence"

    #: Academic and critical interpretations attributed to identifiable
    #: scholars, works, and research publications.
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation"

    #: Interpretations attributed to identifiable theological traditions,
    #: authors, works, and doctrinal frameworks.
    THEOLOGICAL_INTERPRETATION = "theological_interpretation"

    #: Machine-generated suggestions, inferences, patterns, and proposed
    #: relationships. ALWAYS non-authoritative.
    AI_HYPOTHESIS = "ai_hypothesis"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: The closed layer set as plain strings, matching the SQL CHECK constraint
#: exactly (migration 0002). NOTE: this is a set of values in declaration order,
#: NOT a ranking -- no ordering semantics attach to it.
LAYER_VALUES: tuple[str, ...] = (
    EpistemicLayer.SCRIPTURE.value,
    EpistemicLayer.TEXTUAL_OBSERVATION.value,
    EpistemicLayer.LINGUISTIC_OBSERVATION.value,
    EpistemicLayer.HISTORICAL_EVIDENCE.value,
    EpistemicLayer.SCHOLARLY_INTERPRETATION.value,
    EpistemicLayer.THEOLOGICAL_INTERPRETATION.value,
    EpistemicLayer.AI_HYPOTHESIS.value,
)

#: The layer that is always non-authoritative.
NON_AUTHORITATIVE_LAYER = EpistemicLayer.AI_HYPOTHESIS

#: Named conditions used by conditional requirements. Each is evaluated by
#: :func:`_condition_holds`. Documented here so the validator's behaviour is
#: explicit rather than implicit (ADR-0011, refinement 2).
CONDITIONS: Mapping[str, str] = {
    "original_language_text": (
        "the record's text contains non-Latin-script characters (Greek, Hebrew, "
        "Cyrillic, Arabic, etc.), so a Unicode normalisation form is relevant"
    ),
    "dating_present": (
        "the record supplies a dating, so a dating basis is required "
        "(a date without a basis is an assertion)"
    ),
}

@dataclass(frozen=True)
class LayerRequirement:
    """Per-layer field requirements of BKB-DATA-001 section 2.2.

    Attributes:
        any_of: Field groups where at least one member must be present and non-empty.
        all_of: Fields that must all be present and non-empty.
        required_if: Conditional requirements as ``(field, condition, description)``
            triples. The field is required only when *condition* holds. A field
            inapplicable to this layer is never listed, so it is never made
            mandatory for it.
        rationale: Why the requirement exists. Surfaced in validation errors so
            that a contributor learns the rule rather than merely hitting it.
    """

    any_of: tuple[tuple[str, ...], ...] = ()
    all_of: tuple[str, ...] = ()
    required_if: tuple[tuple[str, str, str], ...] = ()
    rationale: str = ""


def _condition_holds(condition: str, fields: Mapping[str, Any]) -> bool:
    """Evaluate a named conditional requirement against *fields*.

    Conditions are a closed, documented set (:data:`CONDITIONS`). An unknown
    condition is an error, never a silent pass.
    """
    if condition == "original_language_text":
        text = fields.get("text")
        if not isinstance(text, str):
            return False
        for ch in text:
            code = ord(ch)
            if code <= 0x24F:
                continue  # basic Latin + Latin extended
            if ch.isspace() or unicodedata.category(ch).startswith(("P", "S", "C")):
                continue  # punctuation, symbols, control: not script evidence
            return True
        return False
    if condition == "dating_present":
        return _present(fields, "dating")
    raise LayerValidationError(
        f"Unknown conditional-requirement condition {condition!r}. Conditions are "
        f"a closed set: {', '.join(sorted(CONDITIONS))}."
    )


import unicodedata  # noqa: E402  (used by _condition_holds above)

#: Per-layer requirements. Mirrors the SQL CHECK constraints of migration 0002.
LAYER_REQUIREMENTS: Mapping[EpistemicLayer, LayerRequirement] = {
    EpistemicLayer.SCRIPTURE: LayerRequirement(
        all_of=("edition_id", "reference", "text", "language"),
        required_if=(
            ("normalisation_form", "original_language_text",
             "original-language text requires a recorded Unicode normalisation form"),
        ),
        rationale=(
            "Scripture is text as attested by a NAMED edition at a valid reference, "
            "in a named language. 'The Bible' is not an edition. Scripture text is "
            "always sourced, never generated."
        ),
    ),
    EpistemicLayer.TEXTUAL_OBSERVATION: LayerRequirement(
        any_of=(("source_dataset", "analyst"), ("observation_method", "observation_type")),
        all_of=("reference", "compared_witnesses", "readings_compared", "source_uri"),
        rationale=(
            "A textual observation COMPARES witnesses: it names the passage, both "
            "sides of the comparison, the readings attributed to their witnesses, "
            "the source of the textual evidence, and an attributed observer. It "
            "never resolves a variant by preference and is never stored as scripture."
        ),
    ),
    EpistemicLayer.LINGUISTIC_OBSERVATION: LayerRequirement(
        any_of=(("source_dataset", "analyst"),),
        all_of=("language", "reference", "observation_type", "analysis"),
        rationale=(
            "A linguistic observation is an analysis performed by an analyst or "
            "recorded in a dataset. It must be attributed."
        ),
    ),
    EpistemicLayer.HISTORICAL_EVIDENCE: LayerRequirement(
        all_of=("evidence_type", "source_uri"),
        required_if=(
            ("dating_basis", "dating_present",
             "a date without a stated basis is an assertion"),
        ),
        rationale=(
            "External evidence must state what kind of evidence it is and cite a "
            "resolvable source. Evidence does not inherit scriptural authority by "
            "association."
        ),
    ),
    EpistemicLayer.SCHOLARLY_INTERPRETATION: LayerRequirement(
        all_of=("scholar", "work", "publication_meta", "position", "supporting_refs",
                "source_uri"),
        rationale=(
            "A scholarly interpretation is academic work: it names the scholar or "
            "author, the work or publication, publication metadata, the attributed "
            "argument, and supporting references. Unattributed scholarship is "
            "rejected. It is NEVER stored as theological_interpretation."
        ),
    ),
    EpistemicLayer.THEOLOGICAL_INTERPRETATION: LayerRequirement(
        any_of=(("tradition", "author"),),
        all_of=("reference", "position", "source_uri"),
        rationale=(
            "An interpretation with no named tradition or author is rejected. "
            "'The church fathers' is not an attribution; a named author with a "
            "named work is. It is NEVER stored as scholarly_interpretation."
        ),
    ),
    EpistemicLayer.AI_HYPOTHESIS: LayerRequirement(
        all_of=("model", "method", "inputs", "generated_at"),
        rationale=(
            "Machine-generated inference must carry its generation provenance: the "
            "model, the method, the input record identifiers, and a timestamp. "
            "Confidence is optional ('if supplied') and NEVER determines the layer: "
            "an ai_hypothesis remains an ai_hypothesis at any confidence score, and "
            "citing sources does not change that."
        ),
    ),
}


def _present(fields: Mapping[str, Any], name: str) -> bool:
    """Return whether *fields[name]* is present and non-empty."""
    if name not in fields:
        return False
    value = fields[name]
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) > 0
    return True


def is_valid_layer(value: Any) -> bool:
    """Return whether *value* is a member of the closed seven-layer set."""
    if isinstance(value, EpistemicLayer):
        return True
    if isinstance(value, str):
        return value in LAYER_VALUES
    return False


def coerce_layer(value: Any) -> EpistemicLayer:
    """Return *value* as an :class:`EpistemicLayer`.

    There is NO DEFAULT LAYER. A missing or unknown layer raises rather than
    being silently defaulted (BKB-DATA-001 rule S6, .clinerules/040 rule 5).

    Raises:
        LayerValidationError: if *value* is absent or not in the closed set.
    """
    if value is None:
        raise LayerValidationError(
            "Epistemic layer is absent. There is no default layer: a record must "
            "declare exactly one. Valid layers: "
            + ", ".join(LAYER_VALUES)
            + "."
        )
    if isinstance(value, EpistemicLayer):
        return value
    if isinstance(value, str):
        try:
            return EpistemicLayer(value)
        except ValueError:
            raise LayerValidationError(
                f"Unknown epistemic layer {value!r}. The layer set is CLOSED. Valid "
                f"layers: {', '.join(LAYER_VALUES)}. Adding a layer requires an "
                f"accepted ADR (ADR-0011)."
            ) from None
    raise LayerValidationError(
        f"Epistemic layer must be a string or EpistemicLayer, got {type(value).__name__}."
    )


def _validate_confidence(fields: Mapping[str, Any], problems: list[str],
                          layer_value: str) -> None:
    """Confidence, where supplied, is a probability. It never determines layer."""
    confidence = fields.get("confidence")
    if confidence is None:
        return  # 'if supplied' for ai_hypothesis; optional elsewhere
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        problems.append(
            f"{layer_value}: 'confidence' must be a number in [0, 1], got "
            f"{type(confidence).__name__}"
        )
    elif not 0.0 <= float(confidence) <= 1.0:
        problems.append(
            f"{layer_value}: 'confidence' must be in [0, 1], got {confidence!r}"
        )


def validate_layer_fields(
    layer: Any, fields: Mapping[str, Any]
) -> tuple[EpistemicLayer, tuple[str, ...]]:
    """Validate *fields* against the requirements for *layer*.

    Conditional requirements (`required_if`) are evaluated explicitly: a field is
    required only when its documented condition holds. Fields not listed for this
    layer are never validated, so they are never made mandatory for it.

    Returns:
        A tuple of the coerced layer and an empty tuple of errors.

    Raises:
        LayerValidationError: if any requirement is unmet. The error names EVERY
            unmet requirement and states the rationale.
    """
    resolved = coerce_layer(layer)
    requirement = LAYER_REQUIREMENTS[resolved]
    problems: list[str] = []

    for name in requirement.all_of:
        if not _present(fields, name):
            problems.append(f"{resolved.value}: required field {name!r} is missing or empty")

    for group in requirement.any_of:
        if not any(_present(fields, name) for name in group):
            options = " or ".join(repr(name) for name in group)
            problems.append(
                f"{resolved.value}: at least one of {options} must be present and non-empty"
            )

    for name, condition, description in requirement.required_if:
        if _condition_holds(condition, fields) and not _present(fields, name):
            problems.append(
                f"{resolved.value}: field {name!r} is required when {CONDITIONS[condition]} "
                f"-- {description}"
            )

    _validate_confidence(fields, problems, resolved.value)

    if problems:
        raise LayerValidationError(
            f"Layer requirements unmet for {resolved.value}. {requirement.rationale}\n  - "
            + "\n  - ".join(problems),
            errors=tuple(problems),
        )
    return resolved, ()


def require_flag(layer: Any) -> bool:
    """Return whether *layer* must be flagged non-authoritative at every boundary.

    Invariant L6. Only ``ai_hypothesis`` requires the flag, and for it the flag is
    mandatory and not removable by the consumer.
    """
    return coerce_layer(layer) is EpistemicLayer.AI_HYPOTHESIS


@dataclass(frozen=True)
class _LayerMetadata:
    layer: str
    non_authoritative: bool
    extra: Mapping[str, Any] = field(default_factory=dict)


def serialise_layer_metadata(layer: Any, fields: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the layer metadata that MUST accompany a serialised record.

    ``layer`` and ``non_authoritative`` are ALWAYS present (BKB-DATA-001 rule X5).
    An export format that cannot represent them may not be used (rule X7).
    """
    resolved = coerce_layer(layer)
    metadata = _LayerMetadata(
        layer=resolved.value,
        non_authoritative=require_flag(resolved),
        extra=dict(fields or {}),
    )
    out: dict[str, Any] = {
        "layer": metadata.layer,
        "non_authoritative": metadata.non_authoritative,
    }
    out.update(metadata.extra)
    return out


def assert_not_promotion(
    current: Any, proposed: Any, evidence: str | None, decided_by: str | None
) -> EpistemicLayer:
    """Guard invariant L7: no layer change by relabelling (ADR-0011).

    There is NO strength comparison -- the layer set has no ordering.

    Rules:
    - Same layer: no-op, permitted.
    - Reclassifying INTO ``ai_hypothesis`` (weakening) is always safe: it requires
      no approval. A claim becoming a hypothesis loses authority; it gains none.
    - Reclassifying AWAY FROM ``ai_hypothesis`` requires BOTH new evidence AND an
      explicit human decision, recorded in the append-only promotion audit. A high
      confidence score or the presence of citations is NOT evidence.
    - Reclassifying between any two non-hypothesis layers also requires evidence
      and a decision: it is a change of claim-type, not a safe direction.
    - ``ai_hypothesis`` -> ``scripture`` is NEVER permitted: scripture text is
      always sourced from a named edition, never generated.

    Returns:
        The coerced proposed layer, if the change is permitted.

    Raises:
        PromotionError: if the change lacks evidence or a decision-maker, or
            targets ``scripture`` from generated content.
    """
    from_layer = coerce_layer(current)
    to_layer = coerce_layer(proposed)

    if from_layer is to_layer:
        return to_layer  # no change

    if to_layer is EpistemicLayer.AI_HYPOTHESIS:
        return to_layer  # weakening to hypothesis: always permitted

    problems: list[str] = []
    if not evidence or not evidence.strip():
        problems.append(
            "new evidence that changes the warrant (a relabel is not a promotion)"
        )
    if not decided_by or not decided_by.strip():
        problems.append("an explicit human decision-maker")
    if problems:
        raise PromotionError(
            f"Layer change from {from_layer.value!r} to {to_layer.value!r} is "
            f"REFUSED. Changing a record's layer requires:\n  - " + "\n  - ".join(problems)
            + "\nRelabelling without evidence and a recorded decision is a Critical "
            "integrity incident (SECURITY.md). Under ADR-0011 the correct path is a "
            "NEW, independently authored and sourced record, never an edit of this one.",
            errors=tuple(problems),
        )
    if to_layer is EpistemicLayer.SCRIPTURE and from_layer is EpistemicLayer.AI_HYPOTHESIS:
        raise PromotionError(
            "Change from 'ai_hypothesis' to 'scripture' is NEVER permitted. "
            "Scripture text is always sourced from a named edition, never generated."
        )
    return to_layer


#: Verification states accepted on derivations (BKB-VERIFY-001 section 3).
DERIVATION_VERIFICATION_STATES = (
    "unverified", "weakly_supported", "supported", "contested", "refuted",
    "unknown", "out_of_scope",
)


@dataclass(frozen=True)
class DerivationRecord:
    """A provenance-preserving derivation linking inputs to outputs.

    Refinement 1 of ADR-0011. Supports MULTIPLE outputs from MULTIPLE inputs and
    preserves every field the derivation model requires. The output layers are
    EXPLICITLY assigned: they are never computed from the input layers (rules
    D1-D2).

    Attributes:
        input_ids: Input record identifiers, each with its ORIGINAL layer.
        output_ids: Output record identifiers, each with its ASSIGNED layer.
        method: The transformation method.
        parameters: Method parameters (optional, recorded when supplied).
        actor: The human or agent responsible.
        created_at: Timestamp.
        tool_identity: Tool/model identity where applicable.
        tool_version: Tool/model version where applicable.
        evidence: Supporting evidence and source provenance.
        verification_state: Verification status, if assessed.
        reviewer: Reviewer, where a review occurred.
        decision_authority: Decision authority, where a decision occurred.
        disagreements: Competing interpretations preserved, never resolved.
    """

    input_ids: tuple[tuple[str, str], ...]
    output_ids: tuple[tuple[str, str], ...]
    method: str
    actor: str
    created_at: str
    parameters: Mapping[str, Any] | None = None
    tool_identity: str | None = None
    tool_version: str | None = None
    evidence: tuple[Mapping[str, Any], ...] = ()
    verification_state: str | None = None
    reviewer: str | None = None
    decision_authority: str | None = None
    disagreements: tuple[Mapping[str, Any], ...] = ()

    @property
    def machine_generated(self) -> bool:
        """Whether a tool/model was involved in producing the outputs."""
        return bool(self.tool_identity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_ids": [[i, l] for i, l in self.input_ids],
            "output_ids": [[o, l] for o, l in self.output_ids],
            "method": self.method,
            "parameters": dict(self.parameters) if self.parameters else None,
            "actor": self.actor,
            "created_at": self.created_at,
            "tool_identity": self.tool_identity,
            "tool_version": self.tool_version,
            "evidence": [dict(e) for e in self.evidence],
            "verification_state": self.verification_state,
            "reviewer": self.reviewer,
            "decision_authority": self.decision_authority,
            "disagreements": [dict(d) for d in self.disagreements],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DerivationRecord":
        """Round-trip deserialisation. Layers in the arrays are validated."""
        def pairs(key: str) -> tuple[tuple[str, str], ...]:
            raw = data.get(key) or []
            out: list[tuple[str, str]] = []
            for item in raw:
                if not (isinstance(item, (list, tuple)) and len(item) == 2):
                    raise DerivationError(
                        f"derivation.{key} entries must be [record_id, layer] pairs"
                    )
                rid, layer = item
                if not (isinstance(rid, str) and rid.strip()):
                    raise DerivationError(f"derivation.{key}: record id must be non-empty")
                try:
                    coerce_layer(layer)  # validates membership
                except LayerValidationError as exc:
                    raise DerivationError(
                        f"derivation.{key}: {exc}", errors=(str(exc),)
                    ) from exc
                out.append((rid, str(layer)))
            return tuple(out)

        return cls(
            input_ids=pairs("input_ids"),
            output_ids=pairs("output_ids"),
            method=str(data.get("method", "")),
            actor=str(data.get("actor", "")),
            created_at=str(data.get("created_at", "")),
            parameters=data.get("parameters"),
            tool_identity=data.get("tool_identity"),
            tool_version=data.get("tool_version"),
            evidence=tuple(data.get("evidence") or ()),
            verification_state=data.get("verification_state"),
            reviewer=data.get("reviewer"),
            decision_authority=data.get("decision_authority"),
            disagreements=tuple(data.get("disagreements") or ()),
        )


def validate_derivation(derivation: DerivationRecord) -> DerivationRecord:
    """Validate a derivation record (BKB-DATA-001 section 2.5, rules D1-D10).

    Checks structure and attribution. It does NOT compute any output layer:
    output layers are explicit inputs to this function, never derived.

    Rules enforced here:
    - D3: multiple outputs are first-class; outputs must be non-empty and unique.
    - D5/D6: outputs are validated; machine-generated non-hypothesis outputs need
      evidence and a decision authority (the auditable human decision).
    - D8: this function never mutates the record; originals are preserved by
      callers appending rather than editing.
    - D10: disagreements are preserved as a sequence of mappings with sources.

    Raises:
        DerivationError: naming every problem.
    """
    problems: list[str] = []

    if not derivation.input_ids:
        problems.append("derivation has no inputs (D: every input record ID is preserved)")
    if not derivation.output_ids:
        problems.append("derivation has no outputs (D3: multiple outputs are first-class)")

    seen_outputs: set[str] = set()
    for rid, layer in derivation.output_ids:
        if rid in seen_outputs:
            problems.append(f"duplicate output record id {rid!r}")
        seen_outputs.add(rid)
        try:
            coerce_layer(layer)
        except LayerValidationError as exc:
            problems.append(f"output {rid!r}: {exc}")

    for rid, layer in derivation.input_ids:
        try:
            coerce_layer(layer)
        except LayerValidationError as exc:
            problems.append(f"input {rid!r}: {exc}")

    for field_name in ("method", "actor", "created_at"):
        if not str(getattr(derivation, field_name) or "").strip():
            problems.append(f"derivation.{field_name} must be a non-empty string")

    if derivation.verification_state is not None:
        if derivation.verification_state not in DERIVATION_VERIFICATION_STATES:
            problems.append(
                f"derivation.verification_state {derivation.verification_state!r} is not "
                f"a known state: {', '.join(DERIVATION_VERIFICATION_STATES)}"
            )
        if derivation.verification_state in ("supported", "refuted", "contested"):
            if not (derivation.reviewer or "").strip():
                problems.append(
                    f"verification_state {derivation.verification_state!r} requires a reviewer"
                )
            if not (derivation.decision_authority or "").strip():
                problems.append(
                    f"verification_state {derivation.verification_state!r} requires a "
                    f"decision authority"
                )

    # D5/D6: machine-generated research begins as ai_hypothesis. A non-hypothesis
    # output produced with tool involvement needs evidence + decision authority.
    if derivation.machine_generated:
        non_ai = [rid for rid, layer in derivation.output_ids
                  if layer != EpistemicLayer.AI_HYPOTHESIS.value]
        if non_ai and not derivation.evidence:
            problems.append(
                "machine-generated derivation producing non-ai_hypothesis output "
                f"{non_ai} requires supporting evidence (D5/D6: citing sources or "
                "confidence does not make an AI proposal authoritative)"
            )
        if non_ai and not (derivation.decision_authority or "").strip():
            problems.append(
                "machine-generated derivation producing non-ai_hypothesis output "
                f"{non_ai} requires a decision authority (D7: auditable human decision)"
            )

    # D10: disagreements preserved with sources.
    for i, item in enumerate(derivation.disagreements):
        if not isinstance(item, Mapping):
            problems.append(f"derivation.disagreements[{i}] must be a mapping with sources")
        elif not item.get("position") or not item.get("source"):
            problems.append(
                f"derivation.disagreements[{i}] must record both a position and its source"
            )

    if problems:
        raise DerivationError(
            "Derivation record invalid:\n  - " + "\n  - ".join(problems),
            errors=tuple(problems),
        )
    return derivation
