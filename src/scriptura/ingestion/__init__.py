"""Ingestion: licence-gated pipeline framework and adapter contract.

No dataset adapter is implemented at M0. Tests use synthetic fixtures only.
"""

from __future__ import annotations

from .adapters.base import (
    ADAPTER_CONTRACT_VERSION,
    CanonicalRecord,
    ConversionReport,
    DatasetAdapter,
)
from .pipeline import ADAPTER_REGISTRY, IngestionResult, IngestionRun, register_adapter, run_ingestion
from .validators import RecordProblem, RecordValidation, validate_record

__all__ = [
    "ADAPTER_CONTRACT_VERSION",
    "CanonicalRecord",
    "ConversionReport",
    "DatasetAdapter",
    "ADAPTER_REGISTRY",
    "IngestionResult",
    "IngestionRun",
    "register_adapter",
    "run_ingestion",
    "RecordProblem",
    "RecordValidation",
    "validate_record",
]
