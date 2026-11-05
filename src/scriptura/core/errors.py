"""Scriptura error hierarchy.

Every error raised by Scriptura derives from :class:`ScripturaError`. Raising a bare
``Exception`` is prohibited by .clinerules/040-engineering.md section 4.

Errors are specific and actionable. A caller must be able to determine what to do next
from the error alone.
"""

from __future__ import annotations

__all__ = [
    "ScripturaError",
    "ConfigurationError",
    "ValidationError",
    "LayerValidationError",
    "ReferenceError",
    "ProvenanceError",
    "LicenceError",
    "LicenceGateError",
    "IngestionError",
    "StorageError",
    "MigrationError",
    "IntegrityError",
    "CapabilityError",
    "SchemaError",
    "UnsupportedSchemaKeywordError",
    "GraphError",
    "SearchError",
    "RetrievalError",
    "ApiError",
    "IndependenceError",
]


class ScripturaError(Exception):
    """Root of the Scriptura error hierarchy."""


class ConfigurationError(ScripturaError):
    """Invalid or missing configuration."""


class ValidationError(ScripturaError):
    """A record failed validation.

    Validation never coerces. A record that fails is rejected, with reasons.
    """

    def __init__(self, message: str, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.errors: tuple[str, ...] = tuple(errors)


class LayerValidationError(ValidationError):
    """An epistemic layer invariant was violated.

    See BKB-DATA-001 section 2 and .clinerules/020-epistemic-layers.md.
    """


class ReferenceError(ScripturaError):
    """A canonical reference is invalid.

    Parsing is strict: an unresolvable book key, an out-of-range chapter, or an
    inverted range raises rather than returning a best guess.
    """


class ProvenanceError(ScripturaError):
    """Provenance is missing, incomplete, or inconsistent.

    No orphan records: every persisted record carries provenance.
    """


class LicenceError(ScripturaError):
    """A licence record is missing, malformed, or inconsistent."""


class LicenceGateError(LicenceError):
    """The ingestion licence gate refused a dataset.

    The gate RAISES; it never warns and continues. The message names EVERY unmet
    condition, not just the first. See ADR-0010 and BKB-CORPUS-001 section 4.
    """

    def __init__(self, dataset_id: str, unmet: tuple[str, ...]) -> None:
        self.dataset_id = dataset_id
        self.unmet_conditions: tuple[str, ...] = tuple(unmet)
        listing = "\n".join(f"  - {c}" for c in self.unmet_conditions)
        super().__init__(
            f"Ingestion of dataset {dataset_id!r} is REFUSED. "
            f"{len(self.unmet_conditions)} condition(s) unmet:\n{listing}"
        )


class IngestionError(ScripturaError):
    """An ingestion operation failed."""


class StorageError(ScripturaError):
    """A storage operation failed."""


class MigrationError(StorageError):
    """A migration failed, or the migration ledger is inconsistent."""


class IntegrityError(ScripturaError):
    """A data-integrity invariant was violated.

    A record whose content does not hash to its recorded digest, a ledger hash
    mismatch, or a layer promotion without an audit record all raise this.
    See SECURITY.md.
    """


class CapabilityError(ScripturaError):
    """A requested capability is not available.

    Raised when a caller PINS an unavailable backend. Absence of an optional
    backend is not an error; it is a degraded mode. Pinning one is.
    """


class SchemaError(ScripturaError):
    """A JSON Schema document is malformed."""


class UnsupportedSchemaKeywordError(SchemaError):
    """A schema uses a keyword the stdlib validator does not support.

    Unsupported keywords are reported as errors, NEVER silently skipped. A schema
    using one fails validation rather than appearing to pass.
    See schemas/README.md.
    """

    def __init__(self, keyword: str, path: str) -> None:
        self.keyword = keyword
        self.path = path
        super().__init__(f"Unsupported JSON Schema keyword {keyword!r} at {path or '<root>'!r}")


class GraphError(ScripturaError):
    """A knowledge graph operation failed."""


class SearchError(ScripturaError):
    """A search operation failed."""


class RetrievalError(ScripturaError):
    """A retrieval operation failed."""


class ApiError(ScripturaError):
    """An API operation failed."""


class IndependenceError(ScripturaError):
    """Scriptura independence was violated.

    Raised if a runtime path acquires a dependency on Gomine. Scriptura must be
    fully functional with no Gomine instance present. See BKB-ARCH-001 section 10.
    """
