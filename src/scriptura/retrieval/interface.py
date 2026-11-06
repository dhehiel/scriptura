"""Provider-independent retrieval interface.

Normative source: BKB-ARCH-001 section 7; ADR-0006.

A retrieval backend is a capability, not a dependency. The interface is defined
here; the FTS5 baseline implements it always; the optional LEANN backend
implements it when installed. Results always carry layer information regardless
of backend. No backend may reorder or filter results in a way that drops layer
information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

__all__ = [
    "BACKEND_FTS5",
    "BACKEND_SEMANTIC",
    "RetrievalResult",
    "RetrievalBackend",
    "BackendStatus",
]


#: Backend identifiers reported by the router. They name WHICH backend served a
#: request; results from different backends are never silently mixed.
BACKEND_FTS5 = "fts5"
BACKEND_SEMANTIC = "leann"


@dataclass(frozen=True)
class RetrievalResult:
    """One retrieval hit, backend-independent.

    Attributes:
        record_id: Stable identifier of the hit record.
        layer: Epistemic layer. ALWAYS present, regardless of backend.
        non_authoritative: The flag. ALWAYS present.
        text: The stored text or statement.
        score: Backend-native score. NOT comparable across backends.
        backend: Which backend produced this hit.
        extra: Backend-specific metadata. Must never carry layer information
            that contradicts ``layer``.
    """

    record_id: str
    layer: str
    non_authoritative: bool
    text: str
    score: float
    backend: str
    extra: Mapping[str, Any] | None = None
    #: Source/provenance locator where the backend knows it (edition or dataset).
    edition_source: str | None = None
    #: Verification status of the hit's record, or None where not recorded at
    #: this level. NEVER invented by a backend.
    verification_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "layer": self.layer,
            "non_authoritative": self.non_authoritative,
            "text": self.text,
            "score": self.score,
            "backend": self.backend,
            "extra": dict(self.extra) if self.extra else None,
            "edition_source": self.edition_source,
            "verification_status": self.verification_status,
        }


@dataclass(frozen=True)
class BackendStatus:
    """Capability report for one backend."""

    backend: str
    available: bool
    reason: str


@runtime_checkable
class RetrievalBackend(Protocol):
    """The contract every retrieval backend implements."""

    @property
    def backend_id(self) -> str:
        """Stable backend identifier, e.g. ``fts5`` or ``leann``."""
        ...

    def is_available(self) -> bool:
        """Whether this backend can serve requests right now."""
        ...

    def status(self) -> BackendStatus:
        """Capability report. Absence is reported, never hidden."""
        ...

    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        layers: Iterable[Any] | None = None,
    ) -> tuple[RetrievalResult, ...]:
        """Search. Every result carries layer information. Never raises on the
        absence of ANOTHER backend."""
        ...
