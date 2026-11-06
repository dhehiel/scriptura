"""The modular knowledge graph over SQLite.

Normative source: BKB-DATA-001 section 6.5; ADR-0007; DKF-ARCH-001 section 10.

The graph is a pair of typed relational tables with layer typing, provenance, and
bounded traversal. There is NO graph database (ADR-0005).

Every edge carries an epistemic layer. A relationship inferred by a model is visibly
different from a relationship asserted by a manuscript. A graph that cannot express
that is worse than no graph, because it launders inference into structure.

Modularity is achieved through registered ``kind`` and ``relation`` vocabularies plus
payload separation, so concerns can be added without altering the storage contract.
An unregistered kind or relation is REJECTED.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from ..core.errors import GraphError
from ..core.hashing import content_hash, mint_identifier
from ..core.layers import (
    EpistemicLayer,
    coerce_layer,
    require_flag,
    validate_derivation,
    DerivationRecord,
)

__all__ = [
    "NODE_KINDS",
    "EDGE_RELATIONS",
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_NODES",
    "Node",
    "Edge",
    "KnowledgeGraph",
    "register_node_kind",
    "register_edge_relation",
]

#: Registered node kinds. Extension is by addition at this seam (BKB-ARCH-001 s9).
NODE_KINDS: frozenset[str] = frozenset({
    "reference", "edition", "witness", "term", "lemma", "person", "place",
    "event", "evidence", "interpretation", "tradition", "hypothesis", "dataset",
    "concept",
    # Seven-layer extensions (ADR-0011): textual criticism and scholarship.
    "reading", "variant", "apparatus", "manuscript", "scholar", "publication",
})

#: Registered edge relations. Extension is by addition at this seam.
EDGE_RELATIONS: frozenset[str] = frozenset({
    "attests", "reads", "parses_as", "translates", "parallels", "quotes", "alludes_to",
    "echoes", "refers_to", "located_in", "participates_in", "dated_to", "interprets",
    "held_by", "derived_from", "supports", "contradicts", "qualifies", "contextualises",
    "proposes_link", "variant_of", "same_lemma", "occurs_in",
    # Typed relations for the seven-layer model (ADR-0011 / BKB-DATA-001 6.5):
    # witness attests reading; textual observation compares readings; linguistic
    # observation analyses a form; scholarly interpretation argues_for an
    # explanation; theological interpretation interprets a passage; AI hypothesis
    # proposes a possible relationship.
    "compares", "argues_for", "proposes", "analyses",
})

#: Default traversal bounds. Unbounded traversal over a graph is both a
#: denial-of-service risk and a correctness risk (DKF-ARCH-001 rule KG5).
DEFAULT_MAX_DEPTH = 4
DEFAULT_MAX_NODES = 500

# Registered at import time; tests may add more through the register_* functions.
_EXTRA_NODE_KINDS: set[str] = set()
_EXTRA_EDGE_RELATIONS: set[str] = set()


def register_node_kind(kind: str) -> str:
    """Register an additional node kind.

    Extension at a defined seam. Every extension must update the corresponding JSON
    Schema and ship tests (BKB-ARCH-001 section 9).
    """
    if not kind or not kind.strip():
        raise GraphError("Node kind must be a non-empty string.")
    _EXTRA_NODE_KINDS.add(kind.strip())
    return kind.strip()


def register_edge_relation(relation: str) -> str:
    """Register an additional edge relation."""
    if not relation or not relation.strip():
        raise GraphError("Edge relation must be a non-empty string.")
    _EXTRA_EDGE_RELATIONS.add(relation.strip())
    return relation.strip()


def _valid_node_kinds() -> frozenset[str]:
    return NODE_KINDS | frozenset(_EXTRA_NODE_KINDS)


def _valid_edge_relations() -> frozenset[str]:
    return EDGE_RELATIONS | frozenset(_EXTRA_EDGE_RELATIONS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Node:
    """A knowledge graph node."""

    id: str
    kind: str
    layer: str
    label: str
    non_authoritative: bool
    source_uri: str
    content_hash: str
    actor: str
    created_at: str
    reference_id: str | None = None
    payload: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "layer": self.layer,
            "label": self.label,
            "non_authoritative": self.non_authoritative,
            "source_uri": self.source_uri,
            "content_hash": self.content_hash,
            "actor": self.actor,
            "created_at": self.created_at,
            "reference_id": self.reference_id,
            "payload": dict(self.payload) if self.payload else None,
        }


@dataclass(frozen=True)
class Edge:
    """A knowledge graph edge."""

    id: str
    source_node_id: str
    target_node_id: str
    relation: str
    layer: str
    non_authoritative: bool
    source_uri: str
    content_hash: str
    actor: str
    created_at: str
    confidence: float | None = None
    payload: Mapping[str, Any] | None = None
    #: Independent dimensions retained on every relationship (BKB-DATA-001 6.5).
    verification_status: str | None = None
    supporting_evidence: str | None = None
    #: Non-ai_hypothesis edges must trace to an authorised derivation record.
    derivation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relation": self.relation,
            "layer": self.layer,
            "non_authoritative": self.non_authoritative,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "supporting_evidence": self.supporting_evidence,
            "derivation_id": self.derivation_id,
            "source_uri": self.source_uri,
            "content_hash": self.content_hash,
            "actor": self.actor,
            "created_at": self.created_at,
            "payload": dict(self.payload) if self.payload else None,
        }


class KnowledgeGraph:
    """The modular knowledge graph.

    Args:
        conn: An open Scriptura connection with migrations applied.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ------------------------------------------------------------------ nodes ----

    def add_node(
        self,
        *,
        kind: str,
        layer: Any,
        label: str,
        source_uri: str,
        actor: str,
        reference_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        node_id: str | None = None,
        created_at: str | None = None,
    ) -> Node:
        """Add a node.

        There is NO DEFAULT LAYER. An unregistered kind raises. An ``ai_hypothesis``
        node is always flagged non-authoritative; the flag is derived from the layer,
        not accepted from the caller, so it cannot be omitted.

        Raises:
            GraphError: if the kind is unregistered, or a required field is empty.
        """
        resolved_kind = (kind or "").strip()
        if resolved_kind not in _valid_node_kinds():
            raise GraphError(
                f"Unregistered node kind {kind!r}. Registered kinds: "
                + ", ".join(sorted(_valid_node_kinds()))
                + ". Extension is by addition at a defined seam and requires a schema "
                "update (BKB-ARCH-001 section 9)."
            )
        resolved_layer = coerce_layer(layer)
        if not label or not label.strip():
            raise GraphError("Node label must be a non-empty string.")
        if not source_uri or not source_uri.strip():
            raise GraphError(
                "Node source_uri must be a non-empty string. An edge or node with no "
                "source is an assertion, not knowledge."
            )
        if not actor or not actor.strip():
            raise GraphError("Node actor must be a non-empty string.")

        payload_json = (
            json.dumps(payload, sort_keys=True, ensure_ascii=False) if payload else None
        )
        digest = content_hash({
            "kind": resolved_kind, "layer": resolved_layer.value, "label": label,
            "reference_id": reference_id, "payload": payload,
        })
        nid = node_id or mint_identifier("scriptura", "node", {
            "kind": resolved_kind, "label": label, "source_uri": source_uri,
        })
        stamp = created_at or _now()

        self.conn.execute(
            "insert into nodes(id, kind, layer, label, reference_id, payload_json, "
            "non_authoritative, source_uri, content_hash, actor, created_at) "
            "values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                nid, resolved_kind, resolved_layer.value, label, reference_id,
                payload_json, 1 if require_flag(resolved_layer) else 0,
                source_uri, digest, actor, stamp,
            ),
        )
        return Node(
            id=nid, kind=resolved_kind, layer=resolved_layer.value, label=label,
            non_authoritative=require_flag(resolved_layer), source_uri=source_uri,
            content_hash=digest, actor=actor, created_at=stamp,
            reference_id=reference_id, payload=dict(payload) if payload else None,
        )

    def get_node(self, node_id: str) -> Node | None:
        row = self.conn.execute(
            "select id, kind, layer, label, reference_id, payload_json, "
            "non_authoritative, source_uri, content_hash, actor, created_at "
            "from nodes where id = ?",
            (node_id,),
        ).fetchone()
        if row is None:
            return None
        return Node(
            id=row[0], kind=row[1], layer=row[2], label=row[3], reference_id=row[4],
            payload=json.loads(row[5]) if row[5] else None,
            non_authoritative=bool(row[6]), source_uri=row[7], content_hash=row[8],
            actor=row[9], created_at=row[10],
        )

    # ------------------------------------------------------------------ edges ----

    def add_edge(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        relation: str,
        layer: Any,
        source_uri: str,
        actor: str,
        confidence: float | None = None,
        payload: Mapping[str, Any] | None = None,
        edge_id: str | None = None,
        created_at: str | None = None,
        verification_status: str | None = None,
        supporting_evidence: str | None = None,
        derivation_id: str | None = None,
    ) -> Edge:
        """Add an edge.

        A link proposed by a discovery strategy is ``ai_hypothesis`` (DKF-ARCH-001
        rule XL1); the flag is derived from the layer. Self-edges are prohibited.

        **No agent writes authoritative edges directly** (ADR-0011, DKF XL2): an
        edge whose layer is NOT ``ai_hypothesis`` must carry a ``derivation_id``
        referencing an authorised derivation record, and the endpoint rule of
        :meth:`validate_edge_layer` must hold.

        Raises:
            GraphError: if the relation is unregistered, the endpoints are identical,
                a required field is empty, confidence is out of range, or a
                non-hypothesis edge lacks an authorised derivation.
        """
        resolved_relation = (relation or "").strip()
        if resolved_relation not in _valid_edge_relations():
            raise GraphError(
                f"Unregistered edge relation {relation!r}. Registered relations: "
                + ", ".join(sorted(_valid_edge_relations()))
                + ". Extension is by addition at a defined seam and requires a schema "
                "update (BKB-ARCH-001 section 9)."
            )
        if source_node_id == target_node_id:
            raise GraphError(
                f"Self-edges are prohibited (ADR-0007). Both endpoints are "
                f"{source_node_id!r}. A relation requiring one needs an ADR."
            )
        resolved_layer = coerce_layer(layer)
        if not source_uri or not source_uri.strip():
            raise GraphError(
                "Edge source_uri must be a non-empty string. An edge with no source is "
                "an assertion, not knowledge."
            )
        if not actor or not actor.strip():
            raise GraphError("Edge actor must be a non-empty string.")
        if confidence is not None and not 0.0 <= float(confidence) <= 1.0:
            raise GraphError(
                f"Edge confidence must be in [0, 1], got {confidence!r}."
            )
        for endpoint in (source_node_id, target_node_id):
            if self.get_node(endpoint) is None:
                raise GraphError(
                    f"Edge endpoint {endpoint!r} does not exist. Foreign keys are "
                    f"enforced; an edge cannot reference a node that is not there."
                )
        # Authoritative (non-hypothesis) edges require an authorised derivation.
        if resolved_layer is not EpistemicLayer.AI_HYPOTHESIS:
            self.validate_edge_layer(
                (source_node_id, target_node_id), resolved_layer,
                derivation=self._load_derivation(derivation_id),
            )

        payload_json = (
            json.dumps(payload, sort_keys=True, ensure_ascii=False) if payload else None
        )
        digest = content_hash({
            "source": source_node_id, "target": target_node_id,
            "relation": resolved_relation, "layer": resolved_layer.value,
            "confidence": confidence, "payload": payload,
        })
        eid = edge_id or mint_identifier("scriptura", "edge", {
            "source": source_node_id, "target": target_node_id,
            "relation": resolved_relation, "source_uri": source_uri,
        })
        stamp = created_at or _now()

        self.conn.execute(
            "insert into edges(id, source_node_id, target_node_id, relation, layer, "
            "non_authoritative, confidence, payload_json, source_uri, content_hash, "
            "actor, created_at, verification_status, supporting_evidence, derivation_id) "
            "values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid, source_node_id, target_node_id, resolved_relation,
                resolved_layer.value, 1 if require_flag(resolved_layer) else 0,
                None if confidence is None else float(confidence), payload_json,
                source_uri, digest, actor, stamp,
                verification_status, supporting_evidence, derivation_id,
            ),
        )
        return Edge(
            id=eid, source_node_id=source_node_id, target_node_id=target_node_id,
            relation=resolved_relation, layer=resolved_layer.value,
            non_authoritative=require_flag(resolved_layer), source_uri=source_uri,
            content_hash=digest, actor=actor, created_at=stamp, confidence=confidence,
            payload=dict(payload) if payload else None,
        )

    def propose_link(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        relation: str,
        source_uri: str,
        actor: str,
        confidence: float | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Edge:
        """Record a link PROPOSED by discovery.

        The layer is ``ai_hypothesis`` by construction. A discovery strategy may not
        emit a link in any other layer (DKF-ARCH-001 rule HL2, prohibition P1). This
        method exists so that the constraint is enforced by the API rather than left to
        the caller.
        """
        return self.add_edge(
            source_node_id=source_node_id, target_node_id=target_node_id,
            relation=relation, layer=EpistemicLayer.AI_HYPOTHESIS,
            source_uri=source_uri, actor=actor, confidence=confidence, payload=payload,
        )

    def _load_derivation(self, derivation_id: str | None) -> DerivationRecord | None:
        """Load and validate a derivation record by id, or None if absent."""
        if not derivation_id:
            return None
        row = self.conn.execute(
            "select id, output_ids, output_layers, input_ids, input_layers, method, "
            "parameters_json, actor, tool_identity, tool_version, created_at, "
            "verification_state, reviewer, decision_authority, evidence_json, "
            "disagreements_json from derivations where id = ?",
            (derivation_id,),
        ).fetchone()
        if row is None:
            raise GraphError(
                f"Derivation {derivation_id!r} does not exist. An authoritative edge "
                f"must trace to an authorised derivation record."
            )
        import json as _json
        data = {
            "input_ids": _json.loads(row[3]), "input_layers": _json.loads(row[4]),
            "output_ids": _json.loads(row[1]), "output_layers": _json.loads(row[2]),
            "method": row[5], "parameters": _json.loads(row[6]) if row[6] else None,
            "actor": row[7], "tool_identity": row[8], "tool_version": row[9],
            "created_at": row[10], "verification_state": row[11],
            "reviewer": row[12], "decision_authority": row[13],
            "evidence": _json.loads(row[14]) if row[14] else [],
            "disagreements": _json.loads(row[15]) if row[15] else [],
        }
        return validate_derivation(DerivationRecord.from_dict(data))

    def validate_edge_layer(
        self,
        endpoint_ids: Sequence[str],
        proposed_layer: Any,
        derivation: DerivationRecord | None = None,
    ) -> EpistemicLayer:
        """Validate an explicitly proposed edge layer (ADR-0011, DKF XL1-XL2).

        There is NO endpoint-inheritance and NO ranking: the layer is an explicit
        input. Rules:

        - ``ai_hypothesis`` edges are proposals and always permitted (XL1).
        - Any other layer requires an authorised derivation record (XL2).
        - If ANY endpoint is ``ai_hypothesis`` (an unverified chain), the edge is
          ``ai_hypothesis`` regardless of what a source says about the endpoints.
        - No edge may take ``scripture`` from a generated chain.

        Raises:
            GraphError: if an endpoint is missing, the derivation is absent or
                invalid, or an endpoint rule is violated.
        """
        proposed = coerce_layer(proposed_layer)
        endpoint_layers: list[str] = []
        for node_id in endpoint_ids:
            node = self.get_node(node_id)
            if node is None:
                raise GraphError(f"Endpoint {node_id!r} does not exist.")
            endpoint_layers.append(node.layer)

        if proposed is EpistemicLayer.AI_HYPOTHESIS:
            return proposed  # a proposal, whatever the endpoints are

        if any(lay == EpistemicLayer.AI_HYPOTHESIS.value for lay in endpoint_layers):
            raise GraphError(
                "A link with an ai_hypothesis endpoint (an unverified chain) must "
                "itself be ai_hypothesis. A source cannot upgrade a hypothesis by "
                "mentioning its endpoints (DKF-ARCH-001 XL1)."
            )
        if derivation is None:
            raise GraphError(
                f"A non-ai_hypothesis edge requires an authorised derivation record "
                f"(proposed layer {proposed.value!r}). No agent writes authoritative "
                f"graph records without validation and verification."
            )
        validate_derivation(derivation)
        if proposed is EpistemicLayer.SCRIPTURE:
            if any("model" in str(d) for d in derivation.evidence) or derivation.machine_generated:
                raise GraphError(
                    "A generated chain may never yield a scripture edge: scripture "
                    "text/relations are always sourced from a named edition."
                )
        return proposed

    def edges_from(
        self, node_id: str, relation: str | None = None,
        layers: Iterable[Any] | None = None,
    ) -> tuple[Edge, ...]:
        """Return outbound edges of *node_id*, optionally filtered."""
        return self._edges("source_node_id", node_id, relation, layers)

    def edges_to(
        self, node_id: str, relation: str | None = None,
        layers: Iterable[Any] | None = None,
    ) -> tuple[Edge, ...]:
        """Return inbound edges of *node_id*, optionally filtered."""
        return self._edges("target_node_id", node_id, relation, layers)

    def _edges(
        self, column: str, node_id: str, relation: str | None,
        layers: Iterable[Any] | None,
    ) -> tuple[Edge, ...]:
        sql = (
            "select id, source_node_id, target_node_id, relation, layer, "
            "non_authoritative, confidence, payload_json, source_uri, content_hash, "
            "actor, created_at, verification_status, supporting_evidence, "
            f"derivation_id from edges where {column} = ?"
        )
        params: list[Any] = [node_id]
        if relation is not None:
            sql += " and relation = ?"
            params.append(relation)
        if layers is not None:
            values = tuple(sorted({coerce_layer(x).value for x in layers}))
            if not values:
                return ()
            sql += f" and layer in ({','.join('?' * len(values))})"
            params.extend(values)
        sql += " order by created_at, id"
        return tuple(self._row_to_edge(row) for row in self.conn.execute(sql, params))

    def _row_to_edge(self, row: sqlite3.Row) -> Edge:
        return Edge(
            id=row[0], source_node_id=row[1], target_node_id=row[2], relation=row[3],
            layer=row[4], non_authoritative=bool(row[5]), confidence=row[6],
            payload=json.loads(row[7]) if row[7] else None, source_uri=row[8],
            content_hash=row[9], actor=row[10], created_at=row[11],
            verification_status=row[12], supporting_evidence=row[13],
            derivation_id=row[14],
        )

    # ----------------------------------------------------------------- counts ----

    def count_nodes(self, layer: Any | None = None) -> int:
        if layer is None:
            return int(self.conn.execute("select count(*) from nodes").fetchone()[0])
        return int(
            self.conn.execute(
                "select count(*) from nodes where layer = ?", (coerce_layer(layer).value,)
            ).fetchone()[0]
        )

    def count_edges(self, layer: Any | None = None) -> int:
        if layer is None:
            return int(self.conn.execute("select count(*) from edges").fetchone()[0])
        return int(
            self.conn.execute(
                "select count(*) from edges where layer = ?", (coerce_layer(layer).value,)
            ).fetchone()[0]
        )
