"""A stdlib JSON Schema subset validator.

Required by ADR-0002: no third-party validator may be a mandatory dependency, and
none is installable in the reference build environment.

Schema documents under ``schemas/`` remain STANDARD JSON Schema draft 2020-12, so
external tooling can validate them fully. This module is Scriptura's internal
enforcement, not a restriction on the format.

Critical design rule: **unsupported keywords are reported as errors, never silently
skipped.** A schema using an unsupported keyword fails validation rather than
appearing to pass. Silently ignoring a keyword would make a schema look enforced when
it is not, which in this project means a licence or layer constraint appearing
enforced when it is not.

See schemas/README.md for the supported subset.
"""

from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

from ..core.errors import SchemaError, UnsupportedSchemaKeywordError

__all__ = [
    "SUPPORTED_KEYWORDS",
    "ANNOTATION_KEYWORDS",
    "UNSUPPORTED_KEYWORDS",
    "Violation",
    "validate",
    "validate_file",
    "load_schema",
    "check_schema_supported",
    "Validator",
]

#: Keywords this validator enforces.
SUPPORTED_KEYWORDS = frozenset({
    "type", "enum", "const", "properties", "required", "additionalProperties",
    "items", "minLength", "maxLength", "minimum", "maximum", "exclusiveMinimum",
    "exclusiveMaximum", "pattern", "$ref", "minItems", "maxItems", "uniqueItems",
})

#: Keywords that carry no assertion and are therefore ignored safely.
ANNOTATION_KEYWORDS = frozenset({
    "$schema", "$id", "$comment", "title", "description", "default", "examples",
    "deprecated", "readOnly", "writeOnly",
})

#: Keywords this validator does NOT support. Their presence is an error.
UNSUPPORTED_KEYWORDS = frozenset({
    "allOf", "anyOf", "oneOf", "not", "if", "then", "else", "$defs", "definitions",
    "patternProperties", "prefixItems", "contains", "dependentRequired",
    "dependentSchemas", "propertyNames", "unevaluatedProperties",
    "unevaluatedItems", "$anchor", "$dynamicRef", "$dynamicAnchor", "contentMediaType",
    "contentEncoding", "contentSchema",
})

_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


@dataclass(frozen=True)
class Violation:
    """One schema violation.

    Attributes:
        path: JSON-pointer-like path to the offending value.
        message: What is wrong.
    """

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path or '<root>'}: {self.message}"


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_type(value: Any, expected: str) -> bool:
    """Check *value* against one JSON Schema type name.

    ``bool`` is checked before ``int`` because ``bool`` subclasses ``int`` in Python.
    ``integer`` accepts an integral float, per JSON Schema. ``number`` accepts both.
    """
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, float) and value.is_integer()
    if expected == "number":
        if isinstance(value, bool):
            return False
        return isinstance(value, (int, float))
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise SchemaError(f"Unknown JSON Schema type name {expected!r}.")


class Validator:
    """Validate documents against a JSON Schema, resolving local ``$ref``.

    Args:
        schema: The root schema document.
        base_dir: Directory used to resolve relative ``$ref`` targets. Required when
            a schema uses ``$ref``.
    """

    def __init__(self, schema: Mapping[str, Any], base_dir: pathlib.Path | None = None) -> None:
        self.schema: Mapping[str, Any] = schema
        self.base_dir = base_dir
        self._cache: dict[pathlib.Path, Mapping[str, Any]] = {}
        check_schema_supported(schema, "<root>")

    # ------------------------------------------------------------------ refs ----

    def _resolve_ref(self, ref: str, current_dir: pathlib.Path | None) -> tuple[Mapping[str, Any], pathlib.Path | None]:
        """Resolve a relative ``$ref`` to a schema document.

        Only whole-document relative file references are supported (for example
        ``"epistemic-layer.schema.json"`` or ``"../core/provenance.schema.json"``).
        Fragment-only and pointer refs are unsupported and raise.
        """
        if ref.startswith("#"):
            raise UnsupportedSchemaKeywordError(
                "$ref", f"fragment ref {ref!r} (only relative file refs are supported)"
            )
        if "://" in ref:
            raise UnsupportedSchemaKeywordError(
                "$ref", f"absolute ref {ref!r} (only relative file refs are supported)"
            )
        if current_dir is None:
            raise SchemaError(
                f"Cannot resolve $ref {ref!r}: no base directory was supplied."
            )
        target = (current_dir / ref).resolve()
        if target in self._cache:
            return self._cache[target], target.parent
        if not target.is_file():
            raise SchemaError(f"$ref target does not exist: {target}")
        document = json.loads(target.read_text(encoding="utf-8"))
        check_schema_supported(document, str(target.name))
        self._cache[target] = document
        return document, target.parent

    # -------------------------------------------------------------- validate ----

    def validate(self, instance: Any) -> tuple[Violation, ...]:
        """Return all violations of *instance* against the root schema."""
        return tuple(self._validate(instance, self.schema, "", self.base_dir))

    def is_valid(self, instance: Any) -> bool:
        return not self._validate(instance, self.schema, "", self.base_dir)

    def _validate(
        self,
        instance: Any,
        schema: Mapping[str, Any],
        path: str,
        current_dir: pathlib.Path | None,
    ) -> Iterator[Violation]:
        if not isinstance(schema, Mapping):
            raise SchemaError(f"Schema at {path or '<root>'} must be an object.")

        for keyword in schema:
            if keyword in SUPPORTED_KEYWORDS or keyword in ANNOTATION_KEYWORDS:
                continue
            if keyword in UNSUPPORTED_KEYWORDS:
                raise UnsupportedSchemaKeywordError(keyword, path)
            raise SchemaError(
                f"Unrecognised JSON Schema keyword {keyword!r} at {path or '<root>'}. "
                f"It is neither supported nor a known annotation, so this validator "
                f"cannot tell whether it would assert something."
            )

        if "$ref" in schema:
            target, target_dir = self._resolve_ref(str(schema["$ref"]), current_dir)
            yield from self._validate(instance, target, path, target_dir)
            # A $ref alongside other keywords: JSON Schema 2020-12 allows this, and
            # the local keywords still apply.

        if "type" in schema:
            expected = schema["type"]
            names = [expected] if isinstance(expected, str) else list(expected)
            if not any(_matches_type(instance, name) for name in names):
                yield Violation(
                    path,
                    f"expected type {' or '.join(names)}, got {_type_name(instance)}",
                )
                return  # further keyword checks are meaningless on a type mismatch

        if "enum" in schema and instance not in schema["enum"]:
            allowed = ", ".join(json.dumps(v, ensure_ascii=False) for v in schema["enum"])
            yield Violation(
                path, f"value {json.dumps(instance, ensure_ascii=False)} is not one of: {allowed}"
            )

        if "const" in schema and instance != schema["const"]:
            yield Violation(
                path, f"expected const {json.dumps(schema['const'], ensure_ascii=False)}"
            )

        if isinstance(instance, str):
            yield from self._validate_string(instance, schema, path)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            yield from self._validate_number(instance, schema, path)
        elif isinstance(instance, list):
            yield from self._validate_array(instance, schema, path, current_dir)
        elif isinstance(instance, dict):
            yield from self._validate_object(instance, schema, path, current_dir)

    def _validate_string(
        self, instance: str, schema: Mapping[str, Any], path: str
    ) -> Iterator[Violation]:
        if "minLength" in schema and len(instance) < schema["minLength"]:
            yield Violation(
                path, f"string length {len(instance)} is below minLength {schema['minLength']}"
            )
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            yield Violation(
                path, f"string length {len(instance)} exceeds maxLength {schema['maxLength']}"
            )
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            yield Violation(
                path, f"string {instance!r} does not match pattern {schema['pattern']!r}"
            )

    def _validate_number(
        self, instance: float, schema: Mapping[str, Any], path: str
    ) -> Iterator[Violation]:
        if "minimum" in schema and instance < schema["minimum"]:
            yield Violation(path, f"{instance} is below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            yield Violation(path, f"{instance} exceeds maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            yield Violation(
                path, f"{instance} is not above exclusiveMinimum {schema['exclusiveMinimum']}"
            )
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            yield Violation(
                path, f"{instance} is not below exclusiveMaximum {schema['exclusiveMaximum']}"
            )

    def _validate_array(
        self,
        instance: list,
        schema: Mapping[str, Any],
        path: str,
        current_dir: pathlib.Path | None,
    ) -> Iterator[Violation]:
        if "minItems" in schema and len(instance) < schema["minItems"]:
            yield Violation(
                path, f"array has {len(instance)} items, below minItems {schema['minItems']}"
            )
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            yield Violation(
                path, f"array has {len(instance)} items, above maxItems {schema['maxItems']}"
            )
        if schema.get("uniqueItems"):
            seen: list[Any] = []
            for item in instance:
                key = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if key in seen:
                    yield Violation(path, "array items must be unique")
                    break
                seen.append(key)
        if "items" in schema:
            item_schema = schema["items"]
            for index, item in enumerate(instance):
                yield from self._validate(item, item_schema, f"{path}[{index}]", current_dir)

    def _validate_object(
        self,
        instance: dict,
        schema: Mapping[str, Any],
        path: str,
        current_dir: pathlib.Path | None,
    ) -> Iterator[Violation]:
        for name in schema.get("required", ()):
            if name not in instance:
                yield Violation(path, f"missing required property {name!r}")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)

        for name, value in instance.items():
            child_path = f"{path}.{name}" if path else name
            if name in properties:
                yield from self._validate(
                    value, properties[name], child_path, current_dir
                )
            elif additional is False:
                known = ", ".join(sorted(properties)) or "(none)"
                yield Violation(
                    child_path,
                    f"additional property {name!r} is not allowed. Known properties: {known}",
                )
            elif isinstance(additional, Mapping):
                yield from self._validate(value, additional, child_path, current_dir)


def check_schema_supported(schema: Mapping[str, Any], path: str = "<root>") -> None:
    """Raise if *schema* uses a keyword this validator does not support.

    Checks the schema document itself, recursively, before any instance is validated.
    This is what makes an unsupported keyword a loud failure rather than a silent gap.
    """
    if not isinstance(schema, Mapping):
        return
    for keyword, value in schema.items():
        if keyword in UNSUPPORTED_KEYWORDS:
            raise UnsupportedSchemaKeywordError(keyword, path)
        if keyword in ("properties", "$defs", "definitions") and isinstance(value, Mapping):
            for name, sub in value.items():
                check_schema_supported(sub, f"{path}.{keyword}.{name}")
        elif keyword == "items" and isinstance(value, Mapping):
            check_schema_supported(value, f"{path}.items")
        elif keyword == "additionalProperties" and isinstance(value, Mapping):
            check_schema_supported(value, f"{path}.additionalProperties")


def load_schema(path: pathlib.Path | str) -> Mapping[str, Any]:
    """Load and pre-flight a schema document.

    Raises:
        SchemaError: if the document is not valid JSON or not an object.
        UnsupportedSchemaKeywordError: if it uses an unsupported keyword.
    """
    resolved = pathlib.Path(path)
    try:
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{resolved} is not valid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise SchemaError(f"{resolved} must contain a JSON object at its root.")
    check_schema_supported(document, resolved.name)
    return document


def validate(
    instance: Any, schema: Mapping[str, Any] | pathlib.Path | str,
    base_dir: pathlib.Path | None = None,
) -> tuple[Violation, ...]:
    """Validate *instance* against *schema*, returning all violations."""
    if isinstance(schema, (str, pathlib.Path)):
        resolved = pathlib.Path(schema)
        schema = load_schema(resolved)
        base_dir = base_dir or resolved.parent
    return Validator(schema, base_dir).validate(instance)


def validate_file(
    instance_path: pathlib.Path | str, schema_path: pathlib.Path | str
) -> tuple[Violation, ...]:
    """Validate a JSON file against a schema file."""
    resolved = pathlib.Path(instance_path)
    try:
        instance = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (Violation("<root>", f"not valid JSON: {exc}"),)
    return validate(instance, schema_path)
