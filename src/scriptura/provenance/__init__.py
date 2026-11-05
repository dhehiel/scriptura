"""Source registry, licence manifest, and the ingestion licence gate.

Depends on ``scriptura.core`` and ``scriptura.schemas``.
"""

from __future__ import annotations

from .licensing import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_REGISTRY_PATH,
    GATE_CONDITIONS,
    GateResult,
    LicensingStore,
    evaluate_gate,
    load_licensing_store,
    require_ingestible,
)

__all__ = [
    "DEFAULT_MANIFEST_PATH",
    "DEFAULT_REGISTRY_PATH",
    "GATE_CONDITIONS",
    "GateResult",
    "LicensingStore",
    "evaluate_gate",
    "load_licensing_store",
    "require_ingestible",
]
