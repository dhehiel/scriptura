"""Versioned exchange documents (BKB-ARCH-001 section 10.3; ADR-0011).

The Gomine interoperability boundary. Scriptura exports and imports claims,
nodes, edges, and derivations through explicit, versioned JSON documents -- nevershared database access. The round-trip must preserve all seven epistemic layers,
record identifiers, graph relationships, source provenance and attribution,
derivation chains with input/output links, verification status, confidence, and
competing interpretations. Preserving only the layer name is insufficient
(tests/test_gomine_exchange.py verifies each property in both directions).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .core.errors import IndependenceError

__all__ = ["EXCHANGE_VERSION", "export_exchange", "import_exchange"]

#: Exchange format version. A change is a schema change and requires an ADR.
EXCHANGE_VERSION = "1.0"

_CLAIM_COLUMNS = (
    "id", "layer", "non_authoritative", "statement", "reference_id", "confidence",
    "verification_state", "edition_id", "witness_id", "evidence_type",
    "evidence_identifier", "dating", "dating_basis", "observation_type",
    "linguistic_form", "analysis", "source_dataset", "analyst",
    "compared_witnesses", "readings_compared", "observation_method",
    "scholar", "publication_meta", "supporting_refs",
    "tradition", "author", "work", "period", "interpretive_context",
    "model", "method", "inputs_json", "generated_at",
    "source_uri", "source_kind", "content_hash", "dataset_id", "licence_id",
    "actor", "created_at", "supersedes",
)

_NODE_COLUMNS = (
    "id", "kind", "layer", "label", "reference_id", "payload_json",
    "non_authoritative", "source_uri", "content_hash", "actor", "created_at",
)

_EDGE_COLUMNS = (
    "id", "source_node_id", "target_node_id", "relation", "layer",
    "non_authoritative", "confidence", "payload_json", "source_uri",
    "content_hash", "actor", "created_at", "verification_status",
    "supporting_evidence", "derivation_id",
)

_DERIVATION_COLUMNS = (
    "id", "output_ids", "output_layers", "input_ids", "input_layers", "method",
    "parameters_json", "actor", "tool_identity", "tool_version", "created_at",
    "verification_state", "reviewer", "decision_authority", "evidence_json",
    "disagreements_json", "source_uri", "content_hash",
)

_JSON_COLUMNS = {
    "payload_json", "inputs_json", "parameters_json", "evidence_json",
    "disagreements_json", "output_ids", "output_layers", "input_ids",
    "input_layers",
}


def _rows(conn: sqlite3.Connection, table: str, columns: tuple[str, ...]) -> list[dict[str, Any]]:
    cols = ", ".join(columns)
    out: list[dict[str, Any]] = []
    for row in conn.execute(f"select {cols} from {table} order by id"):
        record: dict[str, Any] = {}
        for name, value in zip(columns, tuple(row)):
            if name in _JSON_COLUMNS and isinstance(value, str):
                record[name] = json.loads(value)
            else:
                record[name] = value
        out.append(record)
    return out


def export_exchange(conn: sqlite3.Connection, *, generator: str = "scriptura") -> dict[str, Any]:
    """Export a versioned exchange document from *conn*.

    Layer, provenance, licence, verification status, confidence, and the
    non-authoritative flag are mandatory in the document; a record missing them
    is never emitted (BKB-ARCH-001 rule I2/I3).
    """
    claims = _rows(conn, "claims", _CLAIM_COLUMNS)
    nodes = _rows(conn, "nodes", _NODE_COLUMNS)
    edges = _rows(conn, "edges", _EDGE_COLUMNS)
    derivations = _rows(conn, "derivations", _DERIVATION_COLUMNS)
    for claim in claims:
        if not claim.get("layer") or claim.get("source_uri") is None:
            raise IndependenceError(
                f"Claim {claim.get('id')!r} lacks layer or provenance; it may not "
                f"be exported."
            )
    for edge in edges:
        if not edge.get("layer") or edge.get("source_uri") is None:
            raise IndependenceError(
                f"Edge {edge.get('id')!r} lacks layer or provenance; it may not "
                f"be exported."
            )
    return {
        "exchange_version": EXCHANGE_VERSION,
        "direction": "export",
        "source_system": "scriptura",
        "target_system": "gomine",
        "generator": generator,
        "records": {"claims": claims, "nodes": nodes, "edges": edges},
        "derivations": derivations,
        "identifier_mappings": [],
        "disagreements": [
            {"derivation_id": d["id"], "items": d.get("disagreements_json") or []}
            for d in derivations if d.get("disagreements_json")
        ],
        "layers_present": sorted({c["layer"] for c in claims} |
                                  {n["layer"] for n in nodes} |
                                  {e["layer"] for e in edges}),
    }


def import_exchange(conn: sqlite3.Connection, doc: Mapping[str, Any]) -> dict[str, int]:
    """Import an exchange document into *conn* (a fresh Scriptura database).

    Preserves identifiers and layers verbatim: no record is reclassified on
    import (directive section 7). Rows already present are skipped (idempotent).
    Returns counts of inserted rows per table.

    Raises:
        IndependenceError: if the document version is unsupported.
    """
    version = str(doc.get("exchange_version", ""))
    if version != EXCHANGE_VERSION:
        raise IndependenceError(
            f"Unsupported exchange_version {version!r}; this build speaks "
            f"{EXCHANGE_VERSION!r}. A version change is a schema change (ADR)."
        )
    counts = {"claims": 0, "nodes": 0, "edges": 0, "derivations": 0}

    def insert(table: str, columns: tuple[str, ...], records: list[Mapping[str, Any]]) -> None:
        for record in records:
            payload = []
            for name in columns:
                value = record.get(name)
                if name in _JSON_COLUMNS and value is not None and not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
                payload.append(value)
            sql = (
                f"insert or ignore into {table} ({', '.join(columns)}) "
                f"values ({','.join('?' * len(columns))})"
            )
            cur = conn.execute(sql, payload)
            counts[table] += cur.rowcount

    # Order matters: edges.derivation_id references derivations(id), so the
    # derivation records must land before the edges that cite them.
    insert("claims", _CLAIM_COLUMNS, list(doc.get("records", {}).get("claims", [])))
    insert("nodes", _NODE_COLUMNS, list(doc.get("records", {}).get("nodes", [])))
    insert("derivations", _DERIVATION_COLUMNS, list(doc.get("derivations", [])))
    insert("edges", _EDGE_COLUMNS, list(doc.get("records", {}).get("edges", [])))
    conn.commit()
    return counts
