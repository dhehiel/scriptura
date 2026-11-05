"""Content hashing and provenance digests.

Normative source: BKB-DATA-001 section 4.4.

Algorithm is SHA-256 over the canonical byte representation. Canonicalisation is
UTF-8, with the Unicode normalisation form recorded. A record whose content does
not hash to its recorded digest is a data-integrity incident.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any

__all__ = [
    "ALGORITHM",
    "NORMALISATION_FORMS",
    "NORMALISATION_FORM",
    "normalise_text",
    "content_hash",
    "hash_bytes",
    "hash_text",
    "hash_json",
    "parse_digest",
    "verify_digest",
    "mint_identifier",
]

#: The only supported digest algorithm.
ALGORITHM = "sha256"

#: Unicode normalisation forms recognised by Scriptura.
NORMALISATION_FORMS = ("NFC", "NFD", "NFKC", "NFKD")

#: The default normalisation form for original-language text.
#:
#: NFC is the default because it is the composed form, which is what most editions
#: publish and what most tooling expects. The form actually used is ALWAYS recorded
#: alongside the text; it is never inferred. BKB-DATA-001 rule U2.
NORMALISATION_FORM = "NFC"


def normalise_text(text: str, form: str = NORMALISATION_FORM) -> str:
    """Return *text* in Unicode normalisation *form*.

    Normalisation is an EXPLICIT, recorded transformation. Text is never silently
    normalised (BKB-DATA-001 rule U3).

    Raises:
        ValueError: if *form* is not a recognised normalisation form.
    """
    if form not in NORMALISATION_FORMS:
        raise ValueError(
            f"Unknown Unicode normalisation form {form!r}. "
            f"Recognised forms: {', '.join(NORMALISATION_FORMS)}."
        )
    return unicodedata.normalize(form, text)


def hash_bytes(data: bytes) -> str:
    """Return the algorithm-prefixed SHA-256 digest of *data*."""
    return f"{ALGORITHM}:{hashlib.sha256(data).hexdigest()}"


def hash_text(text: str, form: str = NORMALISATION_FORM) -> str:
    """Return the digest of *text* encoded as UTF-8 after normalising to *form*."""
    return hash_bytes(normalise_text(text, form).encode("utf-8"))


def hash_json(value: Any) -> str:
    """Return the digest of *value* serialised canonically.

    Canonicalisation: UTF-8, keys sorted, no insignificant whitespace, and
    ``ensure_ascii=False`` so that original-language text is hashed as itself
    rather than as escape sequences.
    """
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hash_bytes(canonical.encode("utf-8"))


def content_hash(value: Any, form: str = NORMALISATION_FORM) -> str:
    """Return the digest of *value*, choosing text or structural canonicalisation.

    Strings are hashed as text; everything else is hashed as canonical JSON.
    """
    if isinstance(value, str):
        return hash_text(value, form)
    if isinstance(value, (bytes, bytearray)):
        return hash_bytes(bytes(value))
    return hash_json(value)


def parse_digest(digest: str) -> tuple[str, str]:
    """Split an algorithm-prefixed digest into ``(algorithm, hex)``.

    Raises:
        ValueError: if *digest* is not well formed or uses an unsupported algorithm.
    """
    if ":" not in digest:
        raise ValueError(
            f"Malformed digest {digest!r}. Expected the form 'algorithm:hexdigest'."
        )
    algorithm, _, hexdigest = digest.partition(":")
    if algorithm != ALGORITHM:
        raise ValueError(
            f"Unsupported digest algorithm {algorithm!r}. Only {ALGORITHM!r} is supported."
        )
    if not hexdigest or len(hexdigest) != 64:
        raise ValueError(
            f"Malformed {ALGORITHM} digest in {digest!r}. Expected 64 hex characters."
        )
    return algorithm, hexdigest


def verify_digest(value: Any, expected: str, form: str = NORMALISATION_FORM) -> bool:
    """Return whether *value* hashes to *expected*.

    A False result is a data-integrity incident. See SECURITY.md.
    """
    parse_digest(expected)  # validates form before comparison
    return content_hash(value, form) == expected


def mint_identifier(namespace: str, kind: str, seed: Any) -> str:
    """Mint a stable, content-addressable Scriptura identifier.

    Form is ``<namespace>:<kind>:<opaque>`` per BKB-DATA-001 section 5. The opaque
    component is derived from a digest of *seed*, which makes identifiers
    reproducible across independent ingestions of the same source.

    Identifiers are opaque: no semantics are encoded in them beyond namespace and
    kind, and they are never reused.

    Raises:
        ValueError: if *namespace* or *kind* is empty or contains a colon.
    """
    for name, part in (("namespace", namespace), ("kind", kind)):
        if not part:
            raise ValueError(f"Identifier {name} must not be empty.")
        if ":" in part:
            raise ValueError(f"Identifier {name} must not contain ':' (got {part!r}).")
    _, hexdigest = parse_digest(content_hash(seed))
    return f"{namespace}:{kind}:{hexdigest[:32]}"
