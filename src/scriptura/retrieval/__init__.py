"""Optional semantic retrieval over a provider-independent interface.

Depends on ``scriptura.core`` and ``scriptura.search``. LEANN is optional and
import-guarded (ADR-0006, ADR-0002).
"""

from __future__ import annotations

from .interface import (
    BACKEND_FTS5,
    BACKEND_SEMANTIC,
    BackendStatus,
    RetrievalBackend,
    RetrievalResult,
)
from .leann_adapter import (
    LeannAdapter,
    leann_available,
    leann_version,
)
from .router import RetrievalRouter, RouteDecision

__all__ = [
    "BACKEND_FTS5",
    "BACKEND_SEMANTIC",
    "BackendStatus",
    "RetrievalBackend",
    "RetrievalResult",
    "LeannAdapter",
    "leann_available",
    "leann_version",
    "RetrievalRouter",
    "RouteDecision",
]
