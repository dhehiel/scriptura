"""Bounded, layer-filtered graph traversal.

Normative source: ADR-0007 rules 8-10; DKF-ARCH-001 rules KG3-KG5.

Every traversal accepts a LAYER FILTER and reports which layers it traversed. A
traversal never silently merges layers. Depth and node count are bounded: unbounded
traversal over a graph is both a denial-of-service risk and a correctness risk.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from ..core.errors import GraphError
from ..core.layers import EpistemicLayer, coerce_layer
from .model import DEFAULT_MAX_DEPTH, DEFAULT_MAX_NODES, Edge, KnowledgeGraph

__all__ = ["TraversalResult", "traverse", "neighbours", "shortest_path", "layer_summary"]


@dataclass(frozen=True)
class TraversalResult:
    """The outcome of a bounded traversal.

    Attributes:
        visited_node_ids: Node identifiers reached, in visit order.
        edges: Edges traversed.
        layers_traversed: Which layers the traversal actually saw. Reported so that a
            caller can see what it was shown (rule KG3).
        depth_reached: The greatest depth actually reached.
        truncated: Whether the traversal stopped because of a bound. A truncated result
            is reported as truncated; it is never presented as complete.
        truncation_reason: Why it was truncated, if it was.
    """

    visited_node_ids: tuple[str, ...]
    edges: tuple[Edge, ...]
    layers_traversed: tuple[str, ...]
    depth_reached: int
    truncated: bool
    truncation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "visited_node_ids": list(self.visited_node_ids),
            "edges": [edge.to_dict() for edge in self.edges],
            "layers_traversed": list(self.layers_traversed),
            "depth_reached": self.depth_reached,
            "truncated": self.truncated,
            "truncation_reason": self.truncation_reason,
        }


def _resolve_layers(layers: Iterable[Any] | None) -> frozenset[str] | None:
    """Normalise a layer filter to a set of layer values, or ``None`` for all layers.

    ``None`` means the caller explicitly asked for ALL layers. That is a deliberate
    choice, not a silent merge: the result reports which layers were traversed.
    """
    if layers is None:
        return None
    resolved = frozenset(coerce_layer(layer).value for layer in layers)
    if not resolved:
        raise GraphError(
            "A layer filter was supplied but was empty. Pass None to traverse all "
            "layers explicitly, or name at least one layer."
        )
    return resolved


def traverse(
    graph: KnowledgeGraph,
    start_node_id: str,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_nodes: int = DEFAULT_MAX_NODES,
    layers: Iterable[Any] | None = None,
    relations: Iterable[str] | None = None,
    direction: str = "out",
    include_ai_hypothesis: bool = True,
) -> TraversalResult:
    """Traverse outward (or inward, or both) from *start_node_id*, breadth-first.

    Args:
        graph: The graph to traverse.
        start_node_id: Where to start.
        max_depth: Maximum hops. Bounded; must be positive.
        max_nodes: Maximum nodes to visit. Bounded; must be positive.
        layers: Layer filter. ``None`` traverses all layers EXPLICITLY and reports
            which were seen. An empty iterable is an error, never "all layers".
        relations: Restrict to these relations.
        direction: ``out``, ``in``, or ``both``.
        include_ai_hypothesis: When False, ``ai_hypothesis`` edges are excluded even if
            the layer filter would admit them. Provided so that a query for sourced
            relationships cannot accidentally include inference.

    Returns:
        A :class:`TraversalResult`, reporting truncation honestly.

    Raises:
        GraphError: if the start node does not exist, the direction is unknown, or a
            bound is not positive.
    """
    if max_depth < 1:
        raise GraphError(f"max_depth must be at least 1, got {max_depth}.")
    if max_nodes < 1:
        raise GraphError(f"max_nodes must be at least 1, got {max_nodes}.")
    if direction not in ("out", "in", "both"):
        raise GraphError(
            f"direction must be 'out', 'in' or 'both', got {direction!r}."
        )
    if graph.get_node(start_node_id) is None:
        raise GraphError(f"Start node {start_node_id!r} does not exist.")

    allowed_layers = _resolve_layers(layers)
    allowed_relations = frozenset(relations) if relations is not None else None

    visited: list[str] = [start_node_id]
    seen_nodes = {start_node_id}
    collected: list[Edge] = []
    seen_edge_ids: set[str] = set()
    layers_seen: set[str] = set()
    depth_reached = 0
    truncated = False
    reason: str | None = None

    queue: deque[tuple[str, int]] = deque([(start_node_id, 0)])

    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue

        edges: list[Edge] = []
        if direction in ("out", "both"):
            edges.extend(graph.edges_from(node_id, None, allowed_layers))
        if direction in ("in", "both"):
            edges.extend(graph.edges_to(node_id, None, allowed_layers))

        for edge in edges:
            if allowed_relations is not None and edge.relation not in allowed_relations:
                continue
            if not include_ai_hypothesis and edge.layer == EpistemicLayer.AI_HYPOTHESIS.value:
                continue
            layers_seen.add(edge.layer)
            if edge.id not in seen_edge_ids:
                seen_edge_ids.add(edge.id)
                collected.append(edge)

            other = edge.target_node_id if edge.source_node_id == node_id else edge.source_node_id
            if other in seen_nodes:
                continue
            if len(seen_nodes) >= max_nodes:
                truncated = True
                reason = (
                    f"reached the max_nodes bound of {max_nodes}; the traversal is "
                    f"INCOMPLETE"
                )
                queue.clear()
                break
            seen_nodes.add(other)
            visited.append(other)
            queue.append((other, depth + 1))
            depth_reached = max(depth_reached, depth + 1)

    return TraversalResult(
        visited_node_ids=tuple(visited),
        edges=tuple(collected),
        layers_traversed=tuple(sorted(layers_seen)),
        depth_reached=depth_reached,
        truncated=truncated,
        truncation_reason=reason,
    )


def neighbours(
    graph: KnowledgeGraph, node_id: str, *, direction: str = "out",
    relation: str | None = None, layers: Iterable[Any] | None = None,
) -> tuple[tuple[Edge, Any], ...]:
    """Return immediate neighbours as ``(edge, other_node)`` pairs.

    A node's own layer is never merged into the result; each edge carries its own.
    """
    allowed = _resolve_layers(layers)
    edges: list[Edge] = []
    if direction in ("out", "both"):
        edges.extend(graph.edges_from(node_id, relation, allowed))
    if direction in ("in", "both"):
        edges.extend(graph.edges_to(node_id, relation, allowed))
    out: list[tuple[Edge, Any]] = []
    for edge in edges:
        other_id = (
            edge.target_node_id if edge.source_node_id == node_id else edge.source_node_id
        )
        other = graph.get_node(other_id)
        if other is not None:
            out.append((edge, other))
    return tuple(out)


def shortest_path(
    graph: KnowledgeGraph, start_node_id: str, end_node_id: str, *,
    max_depth: int = DEFAULT_MAX_DEPTH, layers: Iterable[Any] | None = None,
) -> tuple[Edge, ...] | None:
    """Return the shortest edge sequence between two nodes, or ``None`` if none exists.

    Bounded by *max_depth*. A ``None`` result means no path was found WITHIN THE
    BOUND, which is recorded as such rather than asserted to be "no path exists".
    """
    if graph.get_node(end_node_id) is None:
        raise GraphError(f"End node {end_node_id!r} does not exist.")
    if start_node_id == end_node_id:
        return ()

    allowed = _resolve_layers(layers)
    predecessors: dict[str, tuple[str, Edge]] = {}
    queue: deque[tuple[str, int]] = deque([(start_node_id, 0)])
    seen = {start_node_id}

    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        edges = list(graph.edges_from(node_id, None, allowed)) + list(
            graph.edges_to(node_id, None, allowed)
        )
        for edge in edges:
            other = (
                edge.target_node_id if edge.source_node_id == node_id
                else edge.source_node_id
            )
            if other in seen:
                continue
            seen.add(other)
            predecessors[other] = (node_id, edge)
            if other == end_node_id:
                path: list[Edge] = []
                cursor = end_node_id
                while cursor in predecessors:
                    previous, step = predecessors[cursor]
                    path.append(step)
                    cursor = previous
                return tuple(reversed(path))
            queue.append((other, depth + 1))
    return None


def layer_summary(graph: KnowledgeGraph) -> dict[str, dict[str, int]]:
    """Return node and edge counts per layer.

    Useful for confirming that a store actually keeps its layers separate, and for
    detecting that a load collapsed them.
    """
    out: dict[str, dict[str, int]] = {}
    for layer in EpistemicLayer:
        out[layer.value] = {
            "nodes": graph.count_nodes(layer),
            "edges": graph.count_edges(layer),
        }
    return out
