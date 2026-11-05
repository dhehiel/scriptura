"""The five epistemic layers.

Normative source: BKB-DATA-001 section 2; ADR-0008;
.clinerules/020-epistemic-layers.md.

Scriptura's foundational architectural commitment. The layer set is CLOSED: adding a
layer requires an accepted ADR.

This module enforces the layer invariants at the type level. The same invariants are
enforced again by SQL CHECK constraints in storage/migrations/0001_bootstrap.sql,
because a constraint that lives only in application code can be bypassed by a future
code path, a script, or a direct SQL client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .errors import LayerValidationError

__all__ = [
    "EpistemicLayer",
    "LAYER_VALUES",
    "LAYER_ORDER",
    "NON_AUTHORITATIVE_LAYER",
    "LayerRequirement",
    "LAYER_REQUIREMENTS",
    "coerce_layer",
    "is_valid_layer",
    "layer_strength",
    "weakest_layer",
    "compose_layer",
    "validate_layer_fields",
    "require_flag",
    "serialise_layer_metadata",
    "assert_not_promotion",
]


class EpistemicLayer(str, Enum):
    """The closed set of epistemic layers.

    Subclasses :class:`str` so that a layer can be compared directly against the
    string values used in SQL CHECK constraints and JSON serialisation, without
    losing enum safety at the Python boundary.
    """

    #: Text of a witness, as attested by a NAMED EDITION. Never generated.
    SCRIPTURE = "scripture"

    #: Material and documentary evidence EXTERNAL to scripture.
    HISTORICAL_EVIDENCE = "historical_evidence"

    #: Morphology, syntax, lexicography, philology.
    LINGUISTIC_OBSERVATION = "linguistic_observation"

    #: Interpretive positions of NAMED traditions and authors.
    THEOLOGICAL_INTERPRETATION = "theological_interpretation"

    #: Machine-generated inference. ALWAYS non-authoritative.
    AI_HYPOTHESIS = "ai_hypothesis"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: The closed layer set, in canonical order (weakest warrant first).
LAYER_ORDER: tuple[EpistemicLayer, ...] = (
    EpistemicLayer.AI_HYPOTHESIS,
    EpistemicLayer.THEOLOGICAL_INTERPRETATION,
    EpistemicLayer.LINGUISTIC_OBSERVATION,
    EpistemicLayer.HISTORICAL_EVIDENCE,
    EpistemicLayer.SCRIPTURE,
)

#: The closed layer set as plain strings, matching the SQL CHECK constraint exactly.
LAYER_VALUES: tuple[str, ...] = tuple(layer.value for layer in LAYER_ORDER)

#: The layer that is always non-authoritative.
NON_AUTHORITATIVE_LAYER = EpistemicLayer.AI_HYPOTHESIS


@dataclass(frozen=True)
class LayerRequirement:
    """The per-layer field requirements of BKB-DATA-001 section 2.2.

    Attributes:
        any_of: Field groups where at least one member must be present and non-empty.
        all_of: Fields that must all be present and non-empty.
        rationale: Why the requirement exists. Surfaced in validation errors so that
            a contributor learns the rule rather than merely hitting it.
    """

    any_of: tuple[tuple[str, ...], ...] = ()
    all_of: tuple[str, ...] = ()
    rationale: str = ""


#: Per-layer requirements. Mirrors the SQL CHECK constraints exactly.
LAYER_REQUIREMENTS: Mapping[EpistemicLayer, LayerRequirement] = {
    EpistemicLayer.SCRIPTURE: LayerRequirement(
        all_of=("edition_id", "reference"),
        rationale=(
            "A scripture record is text as attested by a NAMED EDITION at a valid "
            "reference. 'The Bible' is not an edition. Scripture text is always "
            "sourced, never generated."
        ),
    ),
    EpistemicLayer.HISTORICAL_EVIDENCE: LayerRequirement(
        all_of=("evidence_type", "source_uri"),
        rationale=(
            "External evidence must state what kind of evidence it is and cite a "
            "resolvable source. Evidence does not inherit scriptural authority by "
            "association."
        ),
    ),
    EpistemicLayer.LINGUISTIC_OBSERVATION: LayerRequirement(
        any_of=(("source_dataset", "analyst"),),
        all_of=("observation_type",),
        rationale=(
            "A linguistic observation is an analysis performed by an analyst or "
            "recorded in a dataset. It must be attributed."
        ),
    ),
    EpistemicLayer.THEOLOGICAL_INTERPRETATION: LayerRequirement(
        any_of=(("tradition", "author"),),
        all_of=("source_uri",),
        rationale=(
            "An interpretation with no named tradition or author is rejected. "
            "'The church fathers' is not an attribution; a named author with a "
            "named work is."
        ),
    ),
    EpistemicLayer.AI_HYPOTHESIS: LayerRequirement(
        all_of=("model", "method", "inputs", "confidence", "generated_at"),
        rationale=(
            "Machine-generated inference must carry its generation provenance: the "
            "model, the method, the inputs, a confidence, and a timestamp."
        ),
    ),
}


def is_valid_layer(value: Any) -> bool:
    """Return whether *value* is a member of the closed layer set."""
    if isinstance(value, EpistemicLayer):
        return True
    if isinstance(value, str):
        return value in LAYER_VALUES
    return False


def coerce_layer(value: Any) -> EpistemicLayer:
    """Return *value* as an :class:`EpistemicLayer`.

    There is NO DEFAULT LAYER. A missing or unknown layer raises rather than being
    silently defaulted (BKB-DATA-001 rule S6, .clinerules/040 rule 5).

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
                f"accepted ADR."
            ) from None
    raise LayerValidationError(
        f"Epistemic layer must be a string or EpistemicLayer, got {type(value).__name__}."
    )


def layer_strength(layer: Any) -> int:
    """Return the warrant strength of *layer* as an index into :data:`LAYER_ORDER`.

    The ordering expresses WARRANT, not truth, and is not a scale on which claims
    are scored. Higher means stronger warrant.
    """
    return LAYER_ORDER.index(coerce_layer(layer))


def weakest_layer(layers: Any) -> EpistemicLayer:
    """Return the weakest layer among *layers*.

    Raises:
        LayerValidationError: if *layers* is empty.
    """
    coerced = [coerce_layer(layer) for layer in layers]
    if not coerced:
        raise LayerValidationError("Cannot determine the weakest layer of an empty set.")
    return min(coerced, key=layer_strength)


def compose_layer(layers: Any) -> EpistemicLayer:
    """Return the layer a derived record must take, given its input layers.

    Derived records take the WEAKEST layer of their inputs, unless a stronger
    warrant is explicitly established and recorded (BKB-DATA-001 section 2.4).

    A graph edge inferred from an AI hypothesis is an ``ai_hypothesis`` edge,
    however strong its other endpoints are.
    """
    return weakest_layer(layers)


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


def validate_layer_fields(
    layer: Any, fields: Mapping[str, Any]
) -> tuple[EpistemicLayer, tuple[str, ...]]:
    """Validate *fields* against the requirements for *layer*.

    Returns:
        A tuple of the coerced layer and an empty tuple of errors.

    Raises:
        LayerValidationError: if any requirement is unmet. The error names EVERY
            unmet requirement and states the rationale, so a contributor learns the
            rule rather than merely hitting it.
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

    if resolved is EpistemicLayer.AI_HYPOTHESIS:
        confidence = fields.get("confidence")
        if confidence is not None:
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
                problems.append(
                    "ai_hypothesis: 'confidence' must be a number in [0, 1], got "
                    f"{type(confidence).__name__}"
                )
            elif not 0.0 <= float(confidence) <= 1.0:
                problems.append(
                    f"ai_hypothesis: 'confidence' must be in [0, 1], got {confidence!r}"
                )

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
    """Layer information that must travel with every serialised record."""

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
    """Guard invariant L7: no promotion by relabelling.

    Downgrading is always safe and requires nothing. Upgrading requires BOTH new
    evidence AND an explicit human decision, and must be recorded in the
    append-only promotion audit.

    Returns:
        The coerced proposed layer, if the change is permitted.

    Raises:
        LayerValidationError: if the change is an upgrade lacking evidence or a
            decision-maker, or if it targets ``scripture`` from generated content.
    """
    from_layer = coerce_layer(current)
    to_layer = coerce_layer(proposed)

    if layer_strength(to_layer) <= layer_strength(from_layer):
        return to_layer  # downgrade or no change: always safe

    problems: list[str] = []
    if not evidence or not evidence.strip():
        problems.append(
            "new evidence that changes the warrant (a relabel is not a promotion)"
        )
    if not decided_by or not decided_by.strip():
        problems.append("an explicit human decision-maker")
    if problems:
        raise LayerValidationError(
            f"Layer promotion from {from_layer.value!r} to {to_layer.value!r} is "
            f"REFUSED. Promotion requires:\n  - " + "\n  - ".join(problems)
            + "\nRelabelling without evidence and a recorded decision is a Critical "
            "integrity incident. See SECURITY.md.",
            errors=tuple(problems),
        )
    if to_layer is EpistemicLayer.SCRIPTURE and from_layer is EpistemicLayer.AI_HYPOTHESIS:
        raise LayerValidationError(
            "Promotion from 'ai_hypothesis' to 'scripture' is NEVER permitted. "
            "Scripture text is always sourced from a named edition, never generated."
        )
    return to_layer
