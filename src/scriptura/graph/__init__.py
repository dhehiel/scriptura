"""The modular knowledge graph over SQLite.

Depends on ``scriptura.core`` and ``scriptura.storage``. There is NO graph database
(ADR-0005).
"""

from __future__ import annotations

from .model import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_NODES,
    EDGE_RELATIONS,
    NODE_KINDS,
    Edge,
    KnowledgeGraph,
    Node,
    register_edge_relation,
    register_node_kind,
)
from .queries import (
    TraversalResult,
    layer_summary,
    neighbours,
    shortest_path,
    traverse,
)

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "DEFAULT_MAX_NODES",
    "EDGE_RELATIONS",
    "NODE_KINDS",
    "Edge",
    "KnowledgeGraph",
    "Node",
    "register_edge_relation",
    "register_node_kind",
    "TraversalResult",
    "layer_summary",
    "neighbours",
    "shortest_path",
    "traverse",
]
