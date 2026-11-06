"""Dataset validation rules (BKB-CORPUS-001 section 6).

Every record is validated BEFORE loading. A record that fails is REJECTED, never
coerced. A rejected record is recorded with its reason, never silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..core.errors import ValidationError
from ..core.hashing import content_hash, parse_digest
from ..core.layers import validate_layer_fields
from ..core.reference import Reference, get_book, parse_reference, validate_membership
from ..schemas import Validator, load_schema

__all__ = [
    "RecordProblem",
    "RecordValidation",
    "validate_record",
    "validate_provenance",
    "validate_reference_value",
]

SCHEMA_SUBDIR = "data"


@dataclass(frozen=True)
class RecordProblem:
    record_index: int
    reason: str

    def __str__(self) -> str:
        return f"record {self.record_index}: {self.reason}"


@dataclass(frozen=True)
class RecordValidation:
    accepted: tuple[int, ...]
    rejected: tuple[RecordProblem, ...]

    @property
    def ok(self) -> bool:
        return not self.rejected


def validate_provenance(prov: Mapping[str, Any] | None, index: int) -> list[str]:
    problems: list[str] = []
    if not isinstance(prov, Mapping):
        return [f"record {index}: provenance must be a mapping"]
    for key in ("source_uri", "source_kind", "content_hash", "actor", "created_at"):
        value = prov.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"record {index}: provenance.{key} must be a non-empty string")
    if prov.get("source_kind") not in ("primary", "secondary", "derived", "generated"):
        problems.append(f"record {index}: provenance.source_kind is not a known kind")
    digest = prov.get("content_hash")
    if isinstance(digest, str) and digest.strip():
        try:
            parse_digest(digest)
        except ValueError as exc:
            problems.append(f"record {index}: provenance.content_hash invalid: {exc}")
    return problems


def validate_reference_value(value: Any, index: int) -> list[str]:
    problems: list[str] = []
    if value is None:
        return problems
    try:
        if isinstance(value, Mapping):
            ref = Reference.from_dict(value)
        elif isinstance(value, str):
            ref = parse_reference(value)
        else:
            return [f"record {index}: reference must be a mapping or string"]
        validate_membership(ref)
    except Exception as exc:
        problems.append(f"record {index}: invalid reference: {exc}")
    return problems


def validate_record(record: Mapping[str, Any], index: int) -> list[str]:
    """Validate one canonical record. Returns a list of problems (empty = valid).

    Layer-specific requirements are evaluated against the MERGED view of the
    record: layer ``fields`` plus the canonical-level ``reference``, the
    provenance ``source_uri``, and the ``statement`` (which carries the
    interpretive argument for scholarly and theological records; the spec name
    ``position`` is an alias for it). This lets one requirement table serve all
    seven layers without forcing inapplicable fields to exist.
    """
    problems: list[str] = []
    if not isinstance(record, Mapping):
        return [f"record {index}: record must be a mapping"]
    kind = record.get("kind")
    if kind not in ("corpus", "claim"):
        problems.append(f"record {index}: kind must be 'corpus' or 'claim'")
    layer = record.get("layer")
    raw_fields = record.get("fields")
    if not isinstance(raw_fields, Mapping):
        problems.append(f"record {index}: fields must be a mapping")
        raw_fields = {}
    fields: dict[str, Any] = dict(raw_fields)
    # Canonical-level fields layer requirements may reference.
    reference = record.get("reference")
    if reference is not None:
        fields.setdefault("reference", reference)
    provenance = record.get("provenance")
    if isinstance(provenance, Mapping) and provenance.get("source_uri"):
        fields.setdefault("source_uri", provenance["source_uri"])
    statement = record.get("statement")
    if statement is None:
        statement = raw_fields.get("statement")
    if statement is not None:
        fields.setdefault("statement", statement)
        # The interpretive argument is stored in `statement`; the spec's
        # `position` name is an alias for it.
        fields.setdefault("position", statement)
    try:
        validate_layer_fields(layer, fields)
    except ValidationError as exc:
        problems.append(f"record {index}: {exc}")
    if layer == "scripture" and kind == "corpus":
        text = fields.get("text", "")
        if not isinstance(text, str) or not text.strip():
            problems.append(f"record {index}: scripture text must be non-empty")
    problems.extend(validate_provenance(provenance, index))
    problems.extend(validate_reference_value(record.get("reference"), index))
    return problems
