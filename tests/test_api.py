"""API surface: read-only, loopback default, no writes, guarded FastAPI."""
import json, threading, time, unittest, urllib.error, urllib.request
from scriptura.api import (
    FASTAPI_ADOPTED, build_app, fastapi_available, serve,
)
from scriptura.graph import KnowledgeGraph
from scriptura.search import FtsIndex
from scriptura.storage import apply_migrations, connect

URI, ACTOR, PORT = "synthetic:test", "test", 18799


def setup_db(path):
    conn = connect(path)
    apply_migrations(conn)
    conn.execute("insert into editions(id,key,name,created_at) values ('e','s','s','2026')")
    conn.execute("insert into canon_profiles(id,key,name,description) values ('p','s','s','s')")
    conn.execute("insert into books(id,key,name_en,chapters,testament) values ('b','S','S',1,'ot')")
    conn.execute("insert into canonical_references(id,book_id,canon_profile_id,chapter,display)"
                 " values ('rf','b','p',1,'S 1')")
    FtsIndex(conn).index_corpus_record(record_id="r0", layer="scripture",
                                       text="logos trace", edition_id="e",
                                       reference_display="S 1")
    conn.execute("insert into corpus_records(id,edition_id,reference_id,text,content_hash,"
                 "source_uri,actor,created_at) values ('r0','e','rf','logos trace',"
                 "'sha256:x','s','t','2026')")
    g = KnowledgeGraph(conn)
    node = g.add_node(kind="concept", layer="linguistic_observation", label="n",
                      source_uri="s", actor="t")
    conn.commit()
    conn.close()
    return node.id


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.db = tempfile.NamedTemporaryFile(delete=False, suffix=".db").name
        import os
        os.unlink(cls.db)
        cls.node_id = setup_db(cls.db)
        cls.thread = threading.Thread(
            target=serve, kwargs={"db_path": cls.db, "port": PORT}, daemon=True)
        cls.thread.start()
        time.sleep(1.0)

    def get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_health(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertFalse(body["writes"])

    def test_describe(self):
        status, body = self.get("/describe")
        self.assertEqual(status, 200)
        self.assertEqual(body["counts"]["corpus_records"], 1)
        self.assertFalse(body["writes"])

    def test_search(self):
        status, body = self.get("/search?q=logos")
        self.assertEqual(status, 200)
        self.assertEqual(body["backend"], "fts5")
        self.assertEqual([h["record_id"] for h in body["hits"]], ["r0"])

    def test_traverse_and_node(self):
        status, body = self.get(f"/graph/traverse?node={self.node_id}")
        self.assertEqual(status, 200)
        self.assertIn(self.node_id, body["visited_node_ids"])
        status, body = self.get(f"/graph/node?id={self.node_id}")
        self.assertEqual(body["label"], "n")

    def test_no_writes(self):
        for method in ("POST", "PUT", "DELETE", "PATCH"):
            with self.subTest(method=method):
                req = urllib.request.Request(
                    f"http://127.0.0.1:{PORT}/search?q=x", method=method)
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=10)
                self.assertEqual(ctx.exception.code, 405)

    def test_unknown_route(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/nope", timeout=10)
        self.assertEqual(ctx.exception.code, 404)

    def test_fastapi_gated(self):
        self.assertFalse(FASTAPI_ADOPTED)
        self.assertFalse(fastapi_available())
        with self.assertRaises(RuntimeError):
            build_app("x.db")


if __name__ == "__main__":
    unittest.main()
