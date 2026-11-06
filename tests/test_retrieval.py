"""Retrieval routing, LEANN boundary (absent), degraded mode. R3: 12."""
import unittest
from scriptura.core.errors import CapabilityError
from scriptura.retrieval import (
    BACKEND_FTS5, BACKEND_SEMANTIC, LeannAdapter, RetrievalRouter,
    leann_available, leann_version,
)
from scriptura.search import FtsIndex
from scriptura.storage import apply_migrations, connect

URI, ACTOR = "synthetic:test", "test"


class RetrievalTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()
        apply_migrations(self.conn)
        self.conn.execute(
            "insert into editions(id,key,name,created_at) values ('e','syn','syn','2026')")
        fts = FtsIndex(self.conn)
        fts.index_corpus_record(record_id="r0", layer="scripture",
                                text="logos trace", edition_id="e",
                                reference_display=None)
        self.conn.commit()
        self.router = RetrievalRouter(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_leann_absent(self):
        self.assertFalse(leann_available())
        self.assertIsNone(leann_version())

    def test_statuses(self):
        statuses = {s.backend: s for s in self.router.statuses()}
        self.assertTrue(statuses[BACKEND_FTS5].available)
        self.assertFalse(statuses[BACKEND_SEMANTIC].available)

    def test_default_fts(self):
        hits, decision = self.router.search("logos")
        self.assertEqual(decision.backend, BACKEND_FTS5)
        self.assertEqual([h.record_id for h in hits], ["r0"])
        self.assertTrue(all(h.layer for h in hits))

    def test_pin_unavailable_raises(self):
        with self.assertRaises(CapabilityError):
            self.router.search("logos", backend=BACKEND_SEMANTIC)

    def test_adapter_refuses_without_package(self):
        from scriptura.retrieval import LeannUnavailableError
        with self.assertRaises(LeannUnavailableError):
            LeannAdapter("/nonexistent/index.leann")

    def test_unknown_backend(self):
        from scriptura.core.errors import RetrievalError
        with self.assertRaises(RetrievalError):
            self.router.search("logos", backend="nope")


if __name__ == "__main__":
    unittest.main()
