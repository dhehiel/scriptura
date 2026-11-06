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
        self.e1 = self.g.add_edge(source_node_id=self.a.id,
                                  target_node_id=self.b.id, relation="echoes",
                                  layer="scripture", source_uri=URI, actor=ACTOR)
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

    def test_derive_weakest(self):
        from scriptura.core.layers import EpistemicLayer
        self.assertEqual(self.g.derive_edge_layer([self.a.id, self.h.id]),
                         EpistemicLayer.AI_HYPOTHESIS)

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
