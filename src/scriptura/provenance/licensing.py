"""Licence manifest and source registry loading plus the ingestion licence gate.

Normative source: BKB-CORPUS-001 section 4; ADR-0010; .clinerules/050-data-licensing.

The gate lives in ``provenance``, NOT in ``ingestion``. A gate inside the thing it
gates is not a gate.

The gate RAISES on failure. It never warns and continues. The failure names EVERY
unmet condition, not just the first. It cannot be bypassed by configuration,
environment variable, flag, or code path. It is re-evaluated on every attempt.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..core.errors import LicenceError, LicenceGateError
from ..schemas import Validator, load_schema

__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "DEFAULT_MANIFEST_PATH",
    "GATE_CONDITIONS",
    "GateResult",
    "LicensingStore",
    "load_licensing_store",
    "evaluate_gate",
    "require_ingestible",
]

DEFAULT_REGISTRY_PATH = pathlib.Path("docs/data/source-registry.json")
DEFAULT_MANIFEST_PATH = pathlib.Path("docs/data/licence-manifest.json")

GATE_CONDITIONS = (
    "G1: dataset has an entry in docs/data/source-registry.json",
    "G2: dataset has an entry in docs/data/licence-manifest.json",
    "G3: verification_status is 'verified'",
    "G4: licence verified against a PRIMARY source, with URL and retrieval date",
    "G5: verbatim attribution recorded where the licence requires one",
    "G6: derivative permission recorded",
    "G7: commercial-use permission recorded",
    "G8: share-alike status recorded, with consequences stated",
    "G9: milestone ingestion gate is open",
    "G10: maintainer authorised ingestion OF THIS DATASET, individually",
)

VERIFIED = "verified"


@dataclass(frozen=True)
class GateResult:
    """Outcome of one gate evaluation."""

    dataset_id: str
    permitted: bool
    unmet: tuple[str, ...] = ()
    licence_licence: str | None = None
    share_alike: bool | None = None
    commercial_use_permitted: bool | None = None
    attribution_text: str | None = None
    warnings: tuple[str, ...] = ()

    def raise_if_refused(self) -> "GateResult":
        if not self.permitted:
            raise LicenceGateError(self.dataset_id, self.unmet)
        return self


class LicensingStore:
    """Loaded registry + manifest, with lookup, gate evaluation, consistency."""

    def __init__(
        self,
        registry: Mapping[str, Any],
        manifest: Mapping[str, Any],
        schemas_dir: pathlib.Path | None = None,
    ) -> None:
        self.registry = registry
        self.manifest = manifest
        self.schemas_dir = pathlib.Path(schemas_dir) if schemas_dir else (
            pathlib.Path(__file__).resolve().parents[3] / "schemas"
        )
        self._sources: dict[str, Mapping[str, Any]] = {
            str(s["source_id"]): s for s in registry.get("sources", [])
        }
        self._licences: dict[str, Mapping[str, Any]] = {
            str(lic["licence_id"]): lic for lic in manifest.get("licences", [])
        }
        self._validate_against_schemas()

    def _validate_against_schemas(self) -> None:
        data_dir = self.schemas_dir / "data"
        entry_v = Validator(load_schema(data_dir / "source-registry-entry.schema.json"), data_dir)
        licence_v = Validator(load_schema(data_dir / "licence-record.schema.json"), data_dir)
        problems: list[str] = []
        for source in self.registry.get("sources", []):
            for v in entry_v.validate(source):
                problems.append(f"source {source.get('source_id', '?')}: {v}")
        for lic in self.manifest.get("licences", []):
            for v in licence_v.validate(lic):
                problems.append(f"licence {lic.get('licence_id', '?')}: {v}")
        if problems:
            raise LicenceError(
                "Licence governance records failed schema validation:\n  - "
                + "\n  - ".join(problems)
            )

    def source(self, source_id: str) -> Mapping[str, Any] | None:
        return self._sources.get(source_id)

    def licences_for(self, source_id: str) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            lic for lic in self._licences.values()
            if source_id in (lic.get("applies_to") or [])
        )

    def registry_gate_open(self) -> bool:
        return bool(self.registry.get("ingestion_gate_open", False))

    def _manifest_datasets(self) -> tuple:
        return tuple(self.manifest.get("datasets", []))

    def ingestible_sources(self) -> tuple[str, ...]:
        """Source ids flagged ingestible in the registry.

        This is registry DATA, not a gate decision. The gate re-checks everything.
        """
        return tuple(sid for sid, s in self._sources.items() if bool(s.get("ingestible")))


    def evaluate(
        self, dataset_id: str, authorised: Sequence[str] | None = None
    ) -> GateResult:
        unmet: list[str] = []
        warnings: list[str] = []
        source = self.source(dataset_id)
        if source is None:
            return GateResult(dataset_id=dataset_id, permitted=False, unmet=(GATE_CONDITIONS[0],))
        licences = self.licences_for(dataset_id)
        if not licences:
            unmet.append(GATE_CONDITIONS[1])
        lic = licences[0] if licences else {}
        status = str(source.get("verification_status", ""))
        lic_status = str(lic.get("verification_status", "")) if lic else ""
        if status != VERIFIED or (lic and lic_status != VERIFIED):
            unmet.append(GATE_CONDITIONS[2])
        evidence = str(source.get("evidence_kind", ""))
        lic_evidence = str(lic.get("evidence_kind", "")) if lic else ""
        has_url = bool(source.get("licence_url")) or bool(lic.get("licence_url"))
        has_date = bool(source.get("retrieved_at")) or bool(lic.get("retrieved_at"))
        if evidence != "primary" or not has_url or not has_date:
            unmet.append(GATE_CONDITIONS[3])
        elif lic and lic_evidence != "primary":
            unmet.append(GATE_CONDITIONS[3])
        if lic.get("attribution_required") and not (lic.get("attribution_text") or "").strip():
            unmet.append(GATE_CONDITIONS[4])
        if lic.get("derivatives_permitted") is None:
            unmet.append(GATE_CONDITIONS[5])
        if lic.get("commercial_use_permitted") is None:
            unmet.append(GATE_CONDITIONS[6])
        share_alike = lic.get("share_alike")
        if share_alike is None:
            unmet.append(GATE_CONDITIONS[7])
        elif share_alike and not (lic.get("share_alike_consequence") or "").strip():
            unmet.append(GATE_CONDITIONS[7] + " (consequence unstated)")
        if not self.registry_gate_open():
            unmet.append(GATE_CONDITIONS[8])
        if dataset_id not in set(authorised or ()):
            unmet.append(GATE_CONDITIONS[9])
        permitted = not unmet
        commercial = lic.get("commercial_use_permitted")
        if permitted and commercial is False:
            warnings.append("QUARANTINE REQUIRED: exclude from commercial distribution.")
        if permitted and share_alike:
            warnings.append("SHARE-ALIKE: derivatives inherit upstream licence, NOT Apache 2.0.")
        return GateResult(
            dataset_id=dataset_id, permitted=permitted, unmet=tuple(unmet),
            licence_licence=lic.get("licence"), share_alike=share_alike,
            commercial_use_permitted=commercial,
            attribution_text=(lic.get("attribution_text") or None),
            warnings=tuple(warnings),
        )

    def consistency_problems(self) -> tuple[str, ...]:
        problems: list[str] = []
        for lic_id, lic in self._licences.items():
            for sid in lic.get("applies_to") or []:
                if sid not in self._sources:
                    problems.append(f"licence {lic_id}: applies_to {sid!r}, no registry entry")
        for sid, source in self._sources.items():
            status = source.get("verification_status")
            if status == VERIFIED:
                if source.get("evidence_kind") != "primary":
                    problems.append(f"source {sid}: verified but evidence not primary")
                if not source.get("licence_url") or not source.get("retrieved_at"):
                    problems.append(f"source {sid}: verified but URL/date missing")
            if source.get("ingestible"):
                if status != VERIFIED:
                    problems.append(f"source {sid}: ingestible but status {status!r}")
                for lic in self.licences_for(sid):
                    if lic.get("verification_status") != VERIFIED:
                        problems.append(f"source {sid}: ingestible but licence not verified")
                if not self.registry_gate_open():
                    problems.append(f"source {sid}: ingestible while gate closed")
            if source.get("licence_cleared") and status != VERIFIED:
                problems.append(f"source {sid}: licence_cleared but status {status!r}")
        return tuple(problems)



def load_licensing_store(
    registry_path: pathlib.Path | str | None = None,
    manifest_path: pathlib.Path | str | None = None,
    schemas_dir: pathlib.Path | None = None,
) -> LicensingStore:
    reg_path = pathlib.Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
    man_path = pathlib.Path(manifest_path) if manifest_path else DEFAULT_MANIFEST_PATH
    try:
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LicenceError(f"Source registry not found: {reg_path}") from None
    except json.JSONDecodeError as exc:
        raise LicenceError(f"Source registry is not valid JSON ({reg_path}): {exc}") from exc
    try:
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LicenceError(f"Licence manifest not found: {man_path}") from None
    except json.JSONDecodeError as exc:
        raise LicenceError(f"Licence manifest is not valid JSON ({man_path}): {exc}") from exc
    if not isinstance(registry, dict) or not isinstance(manifest, dict):
        raise LicenceError("Registry and manifest must each be a JSON object.")
    return LicensingStore(registry, manifest, schemas_dir)


def evaluate_gate(
    dataset_id: str,
    authorised: Sequence[str] | None = None,
    registry_path: pathlib.Path | str | None = None,
    manifest_path: pathlib.Path | str | None = None,
    schemas_dir: pathlib.Path | None = None,
) -> GateResult:
    return load_licensing_store(registry_path, manifest_path, schemas_dir).evaluate(
        dataset_id, authorised
    )


def require_ingestible(
    dataset_id: str,
    authorised: Sequence[str] | None = None,
    registry_path: pathlib.Path | str | None = None,
    manifest_path: pathlib.Path | str | None = None,
    schemas_dir: pathlib.Path | None = None,
) -> GateResult:
    """Evaluate the gate and RAISE unless permitted. The single ingestion chokepoint.

    No bypass flag, environment override, or config switch exists — the signature
    has no such parameter, on purpose.
    """
    return evaluate_gate(
        dataset_id, authorised, registry_path, manifest_path, schemas_dir
    ).raise_if_refused()

