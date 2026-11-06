"""Knowledge graph: nodes, edges, traversal, layer filtering. R3: 8."""
import unittest
from scriptura.core.errors import GraphError, LayerValidationError
from scriptura.graph import (
    KnowledgeGraph, layer_summary, neighbours, shortest_path, traverse,
)
from scriptura.storage import apply_migrations, connect

URI, ACTOR = "synthetic:test", "test"


class GraphTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()
        apply_migrations(self.conn)
        self.g = KnowledgeGraph(self.conn)
        self.a = self.g.add_node(kind="reference", layer="scripture",
                                 label="Jhn 1:1", source_uri=URI, actor=ACTOR)
        self.b = self.g.add_node(kind="reference", layer="scripture",
                                 label="Gen 1:1", source_uri=URI, actor=ACTOR)
        self.h = self.g.add_node(kind="hypothesis", layer="ai_hypothesis",
                                 label="echo", source_uri=URI, actor=ACTOR)
        # Authoritative (non-ai) edges require an authorised derivation (XL2).
        import json as _json
        from scriptura.core.hashing import content_hash
        self.derivation_id = "deriv-test-1"
        self.conn.execute(
            "insert into derivations(id,output_ids,output_layers,input_ids,input_layers,"
            "method,actor,created_at,source_uri,content_hash) values (?,?,?,?,?,?,?,?,?,?)",
            (self.derivation_id,
             _json.dumps([["edge-e1", "scripture"]]), _json.dumps(["scripture"]),
             _json.dumps([[self.a.id, "scripture"], [self.b.id, "scripture"]]),
             _json.dumps(["scripture", "scripture"]),
             "edition_assertion", ACTOR, "2026", URI,
             content_hash("edge-e1")),
        )
        self.e1 = self.g.add_edge(source_node_id=self.a.id,
                                  target_node_id=self.b.id, relation="echoes",
                                  layer="scripture", source_uri=URI, actor=ACTOR,
                                  derivation_id=self.derivation_id)
        self.e2 = self.g.propose_link(source_node_id=self.a.id,
                                      target_node_id=self.h.id,
                                      relation="proposes_link", source_uri=URI,
                                      actor=ACTOR, confidence=0.4)

    def tearDown(self):
        self.conn.close()

    def test_counts_and_flags(self):
        self.assertEqual((self.g.count_nodes(), self.g.count_edges()), (3, 2))
        self.assertTrue(self.e2.non_authoritative)
        self.assertEqual(self.e2.layer, "ai_hypothesis")
        self.assertFalse(self.e1.non_authoritative)

    def test_validate_edge_layer_no_inheritance(self):
        # Explicit layer: no endpoint inheritance, no ranking (ADR-0011).
        from scriptura.core.layers import EpistemicLayer
        # a proposal is always permitted, whatever the endpoints are
        self.assertEqual(
            self.g.validate_edge_layer((self.a.id, self.h.id), "ai_hypothesis"),
            EpistemicLayer.AI_HYPOTHESIS)
        # a non-ai edge with an ai_hypothesis endpoint is refused
        with self.assertRaises(GraphError):
            self.g.validate_edge_layer((self.a.id, self.h.id), "scripture")
        # a non-ai edge without a derivation is refused
        with self.assertRaises(GraphError):
            self.g.validate_edge_layer((self.a.id, self.b.id), "scripture")
        # with the authorised derivation it passes
        from scriptura.graph.model import DerivationRecord
        from scriptura.core.layers import validate_derivation
        derivation = DerivationRecord.from_dict({
            "input_ids": [[self.a.id, "scripture"], [self.b.id, "scripture"]],
            "input_layers": ["scripture", "scripture"],
            "output_ids": [["edge-x", "scripture"]],
            "output_layers": ["scripture"],
            "method": "edition_assertion", "actor": ACTOR, "created_at": "2026",
        })
        self.assertEqual(
            self.g.validate_edge_layer((self.a.id, self.b.id), "scripture", derivation),
            EpistemicLayer.SCRIPTURE)

    def test_edge_requires_derivation(self):
        with self.assertRaises(GraphError):
            self.g.add_edge(source_node_id=self.a.id, target_node_id=self.b.id,
                            relation="reads", layer="textual_observation",
                            source_uri=URI, actor=ACTOR)
        with self.assertRaises(GraphError):
            self.g.add_edge(source_node_id=self.a.id, target_node_id=self.b.id,
                            relation="reads", layer="textual_observation",
                            source_uri=URI, actor=ACTOR,
                            derivation_id="nonexistent-derivation")

    def test_traversal_reports_layers(self):
        result = traverse(self.g, self.a.id, direction="both")
        self.assertEqual(len(result.visited_node_ids), 3)
        self.assertEqual(set(result.layers_traversed),
                         {"scripture", "ai_hypothesis"})
        self.assertFalse(result.truncated)

    def test_traversal_excludes_hypothesis(self):
        result = traverse(self.g, self.a.id, direction="both",
                          include_ai_hypothesis=False)
        self.assertEqual(len(result.visited_node_ids), 2)
        self.assertEqual(result.layers_traversed, ("scripture",))

    def test_layer_filter(self):
        result = traverse(self.g, self.a.id, direction="both",
                          layers=["historical_evidence"])
        self.assertEqual(result.visited_node_ids, (self.a.id,))

    def test_bounds(self):
        result = traverse(self.g, self.a.id, direction="both", max_nodes=2)
        self.assertTrue(result.truncated)
        self.assertIsNotNone(result.truncation_reason)
        with self.assertRaises(GraphError):
            traverse(self.g, self.a.id, max_depth=0)

    def test_shortest_path(self):
        path = shortest_path(self.g, self.a.id, self.b.id)
        self.assertEqual([e.id for e in path], [self.e1.id])
        self.assertIsNone(shortest_path(self.g, self.a.id, self.h.id,
                                        layers=["scripture"]))

    def test_neighbours(self):
        pairs = neighbours(self.g, self.a.id)
        self.assertEqual({e.relation for e, _ in pairs},
                         {"echoes", "proposes_link"})

    def test_rejections(self):
        with self.assertRaises(GraphError):
            self.g.add_edge(source_node_id=self.a.id, target_node_id=self.a.id,
                            relation="echoes", layer="scripture",
                            source_uri=URI, actor=ACTOR)
        with self.assertRaises(GraphError):
            self.g.add_edge(source_node_id=self.a.id, target_node_id=self.b.id,
                            relation="invented_rel", layer="scripture",
                            source_uri=URI, actor=ACTOR)
        with self.assertRaises(GraphError):
            self.g.add_node(kind="not_a_kind", layer="scripture", label="x",
                            source_uri=URI, actor=ACTOR)
        with self.assertRaises(LayerValidationError):
            self.g.add_node(kind="concept", layer="nope", label="x",
                            source_uri=URI, actor=ACTOR)
        with self.assertRaises(GraphError):
            self.g.add_node(kind="concept", layer="scripture", label="",
                            source_uri=URI, actor=ACTOR)

    def test_summary(self):
        summary = layer_summary(self.g)
        self.assertEqual(summary["scripture"]["nodes"], 2)
        self.assertEqual(summary["ai_hypothesis"]["edges"], 1)


if __name__ == "__main__":
    unittest.main()
