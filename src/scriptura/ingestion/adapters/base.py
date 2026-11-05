"""Adapter contract: per-dataset conversion of retrieved bytes to canonical records.

Normative source: BKB-CORPUS-001 section 5.

An adapter converts ONE upstream dataset's native format into Scriptura's
canonical record shape. It accepts a path to ALREADY-RETRIEVED bytes and
performs NO network I/O. It resolves NO licences — that is the gate's job
(BKB-CORPUS-001 GT7). It GENERATES no text; it copies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

__all__ = [
    "CanonicalRecord",
    "ConversionReport",
    "DatasetAdapter",
    "ADAPTER_CONTRACT_VERSION",
]

#: Version of the adapter contract. Adapters declare which version they implement
#: so a contract change fails loudly instead of mis-converting silently.
ADAPTER_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True)
class CanonicalRecord:
    """One converted record, ready for validation and loading.

    Attributes:
        layer: Epistemic layer. NEVER defaulted by the adapter (rule A5).
        kind: ``corpus`` (a text record) or ``claim`` (a claim-bearing record).
        fields: Layer-specific fields, e.g. edition/reference/text for a
            ``corpus`` record, or the claim payload for a ``claim`` record.
        provenance: source_uri, retrieved_at, content_hash, dataset_id,
            licence_id, actor, created_at. Complete or the record is rejected.
        manifest: Adapter name and version that produced this record.
    """

    layer: str
    kind: str
    fields: Mapping[str, Any]
    provenance: Mapping[str, Any]
    manifest: Mapping[str, str]


@dataclass(frozen=True)
class ConversionReport:
    """What an adapter run produced, including what it could not convert.

    A rejected input is recorded with its reason. It is NEVER silently dropped
    (rule A7).
    """

    dataset_id: str
    adapter: str
    adapter_version: str
    records: tuple[CanonicalRecord, ...] = ()
    skipped: tuple[Mapping[str, str], ...] = ()
    source_hash: str | None = None
    byte_length: int | None = None

    @property
    def converted(self) -> int:
        return len(self.records)

    @property
    def rejected(self) -> int:
        return len(self.skipped)


class DatasetAdapter(ABC):
    """Abstract base class for all dataset adapters."""

    #: The dataset this adapter serves.
    dataset_id: str = ""
    #: Accepted input format, with version, e.g. ``"osis-2.1"``.
    input_format: str = ""
    #: Adapter implementation version.
    version: str = "0.0.0"

    @property
    def contract_version(self) -> str:
        return ADAPTER_CONTRACT_VERSION

    @abstractmethod
    def convert(self, source_path: str, *, dataset_id: str) -> ConversionReport:
        """Convert already-retrieved bytes at *source_path*.

        Must be deterministic: same input bytes, same records. Must not mutate
        its input. Must not resolve licences. Must not perform network I/O.
        """
        ...
