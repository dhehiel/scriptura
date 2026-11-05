"""JSON Schema validation for Scriptura data structures.

Uses a stdlib subset validator. See schemas/README.md and ADR-0002.
"""

from __future__ import annotations

from .validator import (
    ANNOTATION_KEYWORDS,
    SUPPORTED_KEYWORDS,
    UNSUPPORTED_KEYWORDS,
    Validator,
    Violation,
    check_schema_supported,
    load_schema,
    validate,
    validate_file,
)

__all__ = [
    "ANNOTATION_KEYWORDS",
    "SUPPORTED_KEYWORDS",
    "UNSUPPORTED_KEYWORDS",
    "Validator",
    "Violation",
    "check_schema_supported",
    "load_schema",
    "validate",
    "validate_file",
]
