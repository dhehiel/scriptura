"""Gomine interoperability round trip (BKB-ARCH-001 section 10.3).

Refinement 4 of the seven-layer directive: the exchange test must verify
preservation of ALL of:
  1. all seven epistemic layers
  2. record IDs and graph relationships
  3. source provenance and attribution
  4. derivation chains and input/output links
  5. verification status and confidence
  6. competing interpretations and disagreements
  7. original and derived record classifications
Preserving only the layer name is insufficient. Everything below is asserted in
BOTH directions (export then import into a fresh database).
"""
import json
import os
import sqlite3
import tempfile
import unittest

from scriptura.core.errors import IndependenceError
from scriptura.exchange import EXCHANGE_VERSION, export_exchange, import_exchange
from scriptura.storage import apply_migrations, connect

SEVEN = (
    "scripture", "textual_observation", "linguistic_observation",
    "historical_evidence", "scholarly_interpretation",
    "theological_interpretation", "ai_hypothesis",
)
HASH = "sha256:" + "0" * 64


def _seed(db_path: str) -> sqlite3.Connection:
    conn = connect(db_path)
    apply_migrations(conn)
    conn.execute("insert into editions(id,key,name,created_at) values ('ed1','e1','Edition One','2026')")
    conn.execute("insert into canon_profiles(id,key,name,description) values ('p1','protestant_66','P66','d')")
    conn.execute("insert into books(id,key,name_en,chapters,testament) values ('bk1','Jhn','John',21,'nt')")
    conn.execute(
        "insert into canonical_references(id,book_id,canon_profile_id,chapter,display)"
        " values ('rf1','bk1','p1',1,'Jhn 1')")
    conn.commit()
    return conn


def _insert_claim(conn, cid, layer, statement, **kw):
    base = dict(id=cid, layer=layer, statement=statement, source_uri="synthetic:source",
                source_kind="primary", content_hash=HASH, actor="exchange-test",
                created_at="2026-11-06")
    base.update(kw)
    cols = ", ".join(base)
    marks = ",".join("?" * len(base))
    conn.execute(f"insert into claims ({cols}) values ({marks})", tuple(base.values()))


class GomineExchangeTest(unittest.TestCase):
    def setUp(self):
        fd, self.src_db = tempfile.mkstemp(suffix=".db"); os.close(fd); os.unlink(self.src_db)
        fd, self.dst_db = tempfile.mkstemp(suffix=".db"); os.close(fd); os.unlink(self.dst_db)
        self.src = _seed(self.src_db)
        self._populate()

    def tearDown(self):
        try:
            self.src.close()
        except Exception:
            pass
        for path in (self.src_db, self.dst_db):
            for suffix in ("", "-wal", "-shm"):
                try:
                    os.unlink(path + suffix)
                except OSError:
                    pass

    def _populate(self):
        c = self.src
        # 1. one claim per layer, all seven, complete fields
        _insert_claim(c, "cl-scripture", "scripture", "edition reads X",
                      edition_id="ed1", reference_id="rf1", non_authoritative=0)
        _insert_claim(c, "cl-textual", "textual_observation", "witnesses A/B differ",
                      reference_id="rf1", compared_witnesses="A,B",
                      readings_compared="X (A); Y (B)", analyst="critic",
                      observation_method="collation", non_authoritative=0)
        _insert_claim(c, "cl-linguistic", "linguistic_observation", "form parses nom sg",
                      reference_id="rf1", observation_type="morphology",
                      analysis="nom sg", analyst="parser", non_authoritative=0)
        _insert_claim(c, "cl-historical", "historical_evidence", "inscription dated",
                      evidence_type="inscription", dating="1st c.", dating_basis="palaeo",
                      confidence=0.6, non_authoritative=0)
        _insert_claim(c, "cl-scholarly", "scholarly_interpretation", "Author X argues P",
                      scholar="Author X", work="A Study", publication_meta="Venue 2020",
                      supporting_refs="ref1", non_authoritative=0)
        _insert_claim(c, "cl-theological-A", "theological_interpretation", "Trad A reads T",
                      tradition="Tradition A", author="Author A", work="Work A",
                      reference_id="rf1", verification_state="contested", non_authoritative=0)
        _insert_claim(c, "cl-theological-B", "theological_interpretation", "Trad B reads U",
                      tradition="Tradition B", author="Author B", work="Work B",
                      reference_id="rf1", verification_state="contested", non_authoritative=0)
        _insert_claim(c, "cl-ai", "ai_hypothesis", "model proposes link",
                      model="m-1", method="prompt-hash", inputs_json='["cl-scripture"]',
                      generated_at="2026-11-06", confidence=0.9,
                      verification_state="unverified", non_authoritative=1)

        # 2. nodes and typed edges
        for nid, kind, layer, label, flag in (
            ("nd-witness", "witness", "scripture", "Wit A", 0),
            ("nd-reading", "reading", "textual_observation", "Read X", 0),
            ("nd-scholar", "scholar", "scholarly_interpretation", "Author X", 0),
            ("nd-hypo", "hypothesis", "ai_hypothesis", "Prop", 1),
        ):
            c.execute(
                "insert into nodes(id,kind,layer,label,non_authoritative,source_uri,"
                "content_hash,actor,created_at) values (?,?,?,?,?,?,?,?,?)",
                (nid, kind, layer, label, flag, "synthetic:source", HASH,
                 "exchange-test", "2026-11-06"))

        # derivation authorising the non-ai edges (chains + disagreements)
        c.execute(
            "insert into derivations(id,output_ids,output_layers,input_ids,input_layers,"
            "method,actor,created_at,verification_state,reviewer,decision_authority,"
            "evidence_json,disagreements_json,source_uri,content_hash) "
            "values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("dv-1",
             json.dumps([["ed-attests", "textual_observation"],
                         ["ed-argues", "scholarly_interpretation"]]),
             json.dumps(["textual_observation", "scholarly_interpretation"]),
             json.dumps([["nd-witness", "scripture"], ["nd-reading", "textual_observation"],
                         ["nd-scholar", "scholarly_interpretation"]]),
             json.dumps(["scripture", "textual_observation", "scholarly_interpretation"]),
             "collation+monograph", "exchange-test", "2026-11-06",
             "supported", "reviewer-1", "maintainer",
             json.dumps([[{"record_id": "cl-historical", "source": "inscription"}]]),
             json.dumps([{"position": "reading X", "source": "apparatus 1"},
                         {"position": "reading Y", "source": "apparatus 2"}]),
             "synthetic:source", HASH))
        for eid, src_n, tgt_n, rel, layer, flag, vstat, ev, dvid in (
            ("ed-attests", "nd-witness", "nd-reading", "attests",
             "textual_observation", 0, "supported", "apparatus 1", "dv-1"),
            ("ed-argues", "nd-scholar", "nd-reading", "argues_for",
             "scholarly_interpretation", 0, "supported", "monograph p.4", "dv-1"),
            ("ed-proposes", "nd-hypo", "nd-reading", "proposes",
             "ai_hypothesis", 1, "unverified", None, None),
        ):
            c.execute(
                "insert into edges(id,source_node_id,target_node_id,relation,layer,"
                "non_authoritative,source_uri,content_hash,actor,created_at,"
                "verification_status,supporting_evidence,derivation_id) "
                "values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (eid, src_n, tgt_n, rel, layer, flag, "synthetic:source", HASH,
                 "exchange-test", "2026-11-06", vstat, ev, dvid))
        c.commit()

    def test_exchange_version(self):
        self.assertEqual(EXCHANGE_VERSION, "1.0")
        doc = export_exchange(self.src)
        self.assertEqual(doc["exchange_version"], EXCHANGE_VERSION)
        self.assertEqual(doc["direction"], "export")
        dst = _seed(self.dst_db)
        with self.assertRaises(IndependenceError):
            import_exchange(dst, dict(doc, exchange_version="9.9"))
        dst.close()

    def test_all_seven_layers_round_trip(self):
        """Property 1: all seven layers preserved, both directions."""
        doc = export_exchange(self.src)
        self.assertEqual(set(doc["layers_present"]), set(SEVEN))
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        layers = {r[0] for r in dst.execute("select distinct layer from claims")}
        layers |= {r[0] for r in dst.execute("select distinct layer from nodes")}
        layers |= {r[0] for r in dst.execute("select distinct layer from edges")}
        self.assertEqual(layers, set(SEVEN))
        dst.close()

    def test_record_ids_and_graph_relationships_preserved(self):
        """Property 2."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        src_claims = sorted(r[0] for r in self.src.execute("select id from claims"))
        dst_claims = sorted(r[0] for r in dst.execute("select id from claims"))
        self.assertEqual(src_claims, dst_claims)
        src_edges = {r[0]: (r[1], r[2], r[3]) for r in
                     self.src.execute("select id,source_node_id,target_node_id,relation from edges")}
        dst_edges = {r[0]: (r[1], r[2], r[3]) for r in
                     dst.execute("select id,source_node_id,target_node_id,relation from edges")}
        self.assertEqual(src_edges, dst_edges)
        self.assertIn(("nd-witness", "nd-reading", "attests"), dst_edges.values())
        dst.close()

    def test_provenance_and_attribution_preserved(self):
        """Property 3."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        row = dst.execute(
            "select source_uri, source_kind, content_hash, actor from claims where id='cl-scholarly'").fetchone()
        self.assertEqual(tuple(row), ("synthetic:source", "primary", HASH, "exchange-test"))
        row = dst.execute(
            "select scholar, work, publication_meta from claims where id='cl-scholarly'").fetchone()
        self.assertEqual(tuple(row), ("Author X", "A Study", "Venue 2020"))
        dst.close()

    def test_derivation_chain_and_links_preserved(self):
        """Property 4: derivation with input/output ids AND layers."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        row = dst.execute(
            "select input_ids, input_layers, output_ids, output_layers, method, actor "
            "from derivations where id='dv-1'").fetchone()
        self.assertEqual(json.loads(row[0]),
                         [["nd-witness", "scripture"],
                          ["nd-reading", "textual_observation"],
                          ["nd-scholar", "scholarly_interpretation"]])
        self.assertEqual(json.loads(row[1]),
                         ["scripture", "textual_observation", "scholarly_interpretation"])
        self.assertEqual(json.loads(row[2]),
                         [["ed-attests", "textual_observation"],
                          ["ed-argues", "scholarly_interpretation"]])
        self.assertEqual(json.loads(row[3]),
                         ["textual_observation", "scholarly_interpretation"])
        self.assertEqual(row[4], "collation+monograph")
        self.assertEqual(row[5], "exchange-test")
        self.assertEqual(
            dst.execute("select derivation_id from edges where id='ed-attests'").fetchone()[0],
            "dv-1")
        dst.close()

    def test_verification_status_and_confidence_preserved(self):
        """Property 5."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        self.assertEqual(
            dst.execute("select confidence from claims where id='cl-historical'").fetchone()[0], 0.6)
        self.assertEqual(
            dst.execute("select verification_state from claims where id='cl-theological-A'").fetchone()[0],
            "contested")
        self.assertEqual(
            dst.execute("select verification_state from claims where id='cl-ai'").fetchone()[0],
            "unverified")
        self.assertEqual(
            dst.execute("select verification_status from edges where id='ed-attests'").fetchone()[0],
            "supported")
        row = dst.execute(
            "select verification_state, reviewer, decision_authority from derivations where id='dv-1'").fetchone()
        self.assertEqual(tuple(row), ("supported", "reviewer-1", "maintainer"))
        dst.close()

    def test_competing_interpretations_and_disagreements_preserved(self):
        """Property 6: both theological positions AND the derivation's disputes."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        traditions = sorted(
            r[0] for r in dst.execute(
                "select tradition from claims where layer='theological_interpretation'"))
        self.assertEqual(traditions, ["Tradition A", "Tradition B"])
        row = dst.execute(
            "select disagreements_json from derivations where id='dv-1'").fetchone()
        items = json.loads(row[0])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["position"], "reading X")
        self.assertEqual(items[0]["source"], "apparatus 1")
        self.assertEqual(items[1]["position"], "reading Y")
        self.assertEqual(items[1]["source"], "apparatus 2")
        dst.close()

    def test_original_and_derived_classifications_preserved(self):
        """Property 7: nothing is reclassified on import."""
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        import_exchange(dst, doc)
        row = dst.execute(
            "select layer, non_authoritative, confidence from claims where id='cl-ai'").fetchone()
        self.assertEqual(row[0], "ai_hypothesis")
        self.assertEqual(row[1], 1)
        self.assertEqual(row[2], 0.9)  # high confidence does NOT change the layer
        self.assertEqual(
            dst.execute("select layer from claims where id='cl-scholarly'").fetchone()[0],
            "scholarly_interpretation")
        self.assertEqual(
            dst.execute("select layer from claims where id='cl-theological-A'").fetchone()[0],
            "theological_interpretation")
        self.assertEqual(
            dst.execute("select layer from claims where id='cl-textual'").fetchone()[0],
            "textual_observation")
        # derived edge keeps its assigned layer (not inherited from endpoints)
        self.assertEqual(
            dst.execute("select layer from edges where id='ed-argues'").fetchone()[0],
            "scholarly_interpretation")
        dst.close()

    def test_round_trip_idempotent_and_counts(self):
        doc = export_exchange(self.src)
        dst = _seed(self.dst_db)
        counts = import_exchange(dst, doc)
        self.assertEqual(counts["claims"], 8)
        self.assertEqual(counts["nodes"], 4)
        self.assertEqual(counts["edges"], 3)
        self.assertEqual(counts["derivations"], 1)
        counts2 = import_exchange(dst, doc)
        self.assertEqual(sum(counts2.values()), 0)
        dst.close()

    def test_schema_refuses_null_provenance(self):
        # provenance is NOT NULL at the schema level, so an unprovenanced record
        # cannot exist to be exported (property 3 is enforced structurally)
        with self.assertRaises(sqlite3.IntegrityError):
            self.src.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,"
                "actor,created_at) values ('cl-null','ai_hypothesis','s',NULL,'generated',"
                "'sha256:x','a','2026')")


if __name__ == "__main__":
    unittest.main()
