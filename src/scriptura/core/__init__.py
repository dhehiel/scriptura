"""Scriptura core: references, epistemic layers, hashing, and errors.

This package depends on NOTHING else within ``scriptura`` and performs no database
I/O and no network I/O (BKB-ARCH-001 section 4.2).
"""

from __future__ import annotations

from . import errors, hashing, layers, reference, text
from .errors import ScripturaError
from .hashing import content_hash, mint_identifier, normalise_text, verify_digest
from .text import fold_diacritics, strip_marks
from .layers import (
    LAYER_VALUES,
    EpistemicLayer,
    DerivationRecord,
    coerce_layer,
    require_flag,
    serialise_layer_metadata,
    validate_derivation,
    validate_layer_fields,
)
from .reference import (
    CANON_PROFILES,
    DEFAULT_CANON_PROFILE,
    Reference,
    parse_reference,
    parse_references,
)

__all__ = [
    "errors",
    "hashing",
    "layers",
    "reference",
    "text",
    "ScripturaError",
    "content_hash",
    "mint_identifier",
    "normalise_text",
    "verify_digest",
    "fold_diacritics",
    "strip_marks",
    "LAYER_VALUES",
    "EpistemicLayer",
    "DerivationRecord",
    "coerce_layer",
    "require_flag",
    "serialise_layer_metadata",
    "validate_derivation",
    "validate_layer_fields",
    "CANON_PROFILES",
    "DEFAULT_CANON_PROFILE",
    "Reference",
    "parse_reference",
    "parse_references",
]
