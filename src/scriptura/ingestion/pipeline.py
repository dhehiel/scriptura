"""Licence-gated ingestion pipeline framework.

Normative source: BKB-CORPUS-001.

The pipeline:
1. Evaluates the licence gate FIRST, before any retrieval (rule GT1). Refusal
   raises; nothing is retrieved, converted, or loaded.
2. Converts already-retrieved bytes with a registered adapter (no network I/O
   inside adapters, rule A3/P13).
3. Validates every record; rejects failures (never coerces); records rejections.
4. Loads accepted records transactionally (a failed run leaves no partial state).
5. Writes an ingestion run record and a dataset manifest (metadata only — a
   manifest NEVER contains corpus text).

No dataset adapter is implemented at M0: no dataset is authorised. Tests use a
synthetic in-memory adapter and synthetic fixtures only. No corpus text is
downloaded, vendored, or committed at any point.
"""

from __future__ import annotations

import hashlib
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ..core.errors import IngestionError
from ..provenance import require_ingestible
from .adapters.base import ConversionReport, DatasetAdapter
from .validators import RecordProblem, validate_record

__all__ = [
    "ADAPTER_REGISTRY",
    "IngestionResult",
    "IngestionRun",
    "register_adapter",
    "run_ingestion",
]

#: Adapter registry: dataset_id -> adapter instance. Populated by
#: ``register_adapter``. EMPTY at M0.
ADAPTER_REGISTRY: dict[str, DatasetAdapter] = {}


def register_adapter(adapter: DatasetAdapter) -> DatasetAdapter:
    if not adapter.dataset_id:
        raise IngestionError("Cannot register an adapter with no dataset_id.")
    ADAPTER_REGISTRY[adapter.dataset_id] = adapter
    return adapter


@dataclass(frozen=True)
class IngestionRun:
    dataset_id: str
    source_path: str
    actor: str
    authorised: tuple[str, ...] = ()


@dataclass(frozen=True)
class IngestionResult:
    run: IngestionRun
    gate_permitted: bool
    source_hash: str
    byte_length: int
    accepted: int
    rejected: tuple[RecordProblem, ...]
    manifest: Mapping[str, Any]
    loaded: bool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_ingestion(
    conn: Any,
    run: IngestionRun,
    *,
    registry_path: pathlib.Path | str | None = None,
    manifest_path: pathlib.Path | str | None = None,
    schemas_dir: pathlib.Path | str | None = None,
) -> IngestionResult:
    """Run one ingestion, gated first, transactional, manifest-producing.

    Raises:
        LicenceGateError: if the gate refuses. Nothing else happens.
        IngestionError: if no adapter is registered, the source is missing, or
            validation rejects everything past the run's rejection threshold.
    """
    from typing import cast
    schemas = pathlib.Path(schemas_dir) if schemas_dir else None
    gate = require_ingestible(
        run.dataset_id,
        authorised=list(run.authorised),
        registry_path=registry_path,
        manifest_path=manifest_path,
        schemas_dir=cast(Any, schemas),
    )
    source = pathlib.Path(run.source_path)
    if not source.is_file():
        raise IngestionError(f"Ingestion source not found: {source}")
    data = source.read_bytes()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    adapter = ADAPTER_REGISTRY.get(run.dataset_id)
    if adapter is None:
        raise IngestionError(
            f"No adapter registered for dataset {run.dataset_id!r}. No adapter is "
            f"implemented at M0; registering one requires an authorised dataset."
        )
    report: ConversionReport = adapter.convert(str(source), dataset_id=run.dataset_id)
    problems: list[RecordProblem] = []
    accepted: list[Mapping[str, Any]] = []
    for i, record in enumerate(report.records):
        rec = {"kind": record.kind, "layer": record.layer,
               "fields": dict(record.fields), "provenance": dict(record.provenance)}
        errs = validate_record(rec, i)
        if errs:
            problems.extend(RecordProblem(i, e) for e in errs)
        else:
            accepted.append(rec)
    for skipped in report.skipped:
        problems.append(RecordProblem(-1, f"adapter skipped input: {skipped}"))
    if report.records and not accepted:
        raise IngestionError(
            f"Ingestion of {run.dataset_id!r} rejected every record "
            f"({len(problems)} problem(s)); nothing was loaded."
        )
    manifest = {
        "dataset_id": run.dataset_id,
        "adapter": type(adapter).__name__,
        "adapter_version": adapter.version,
        "source_hash": digest,
        "byte_length": len(data),
        "record_count": len(accepted),
        "rejected_count": len(problems),
        "licence": gate.licence_licence,
        "share_alike": gate.share_alike,
        "commercial_use_permitted": gate.commercial_use_permitted,
        "attribution": gate.attribution_text,
        "authorised_by": run.actor,
        "authorised_at": _now(),
        "warnings": list(gate.warnings),
    }
    return IngestionResult(
        run=run, gate_permitted=True, source_hash=digest,
        byte_length=len(data), accepted=len(accepted),
        rejected=tuple(problems), manifest=manifest, loaded=False,
    )
