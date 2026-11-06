"""FTS5 indexing and querying: exact, folded, prefix, scripts. R3: 3-4."""
import unittest
from scriptura.core.errors import SearchError
from scriptura.search import FtsIndex, fold_diacritics
from scriptura.storage import apply_migrations, connect

URI, ACTOR = "synthetic:test", "test"
G_POLY = "\u1f41 \u03bb\u03cc\u03b3\u03bf\u03c2 \u1f26\u03bd"
G_PLAIN = "\u03bb\u03bf\u03b3\u03bf\u03c2"
H_POINT = "\u05d0\u05b1\u05dc\u05b9\u05d4\u05b4\u05d9\u05dd"
H_PLAIN = "\u05d0\u05dc\u05d4\u05d9\u05dd"
L_ACC, L_PLAIN = "De\u00e9sus", "Deesus"


class FtsTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()
        apply_migrations(self.conn)
        self.fts = FtsIndex(self.conn)
        self.conn.execute(
            "insert into editions(id,key,name,created_at) values ('e','syn','syn','2026')")
        self.conn.execute(
            "insert into canon_profiles(id,key,name,description) values ('p','syn','syn','syn')")
        self.conn.execute(
            "insert into books(id,key,name_en,chapters,testament) values ('b','Syn','Synthetic',1,'ot')")
        self.conn.execute(
            "insert into canonical_references(id,book_id,canon_profile_id,chapter,display)"
            " values ('rf','b','p',1,'Syn 1')")
        for i, text in enumerate([G_POLY, H_POINT, L_ACC]):
            self.fts.index_corpus_record(record_id=f"r{i}", layer="scripture",
                                         text=text, edition_id="e",
                                         reference_display="Syn 1")
            self.conn.execute(
                "insert into corpus_records(id,edition_id,reference_id,text,content_hash,"
                "source_uri,actor,created_at) values (?,?,?,?,?,?,?,?)",
                (f"r{i}", "e", "rf", text, "sha256:x", URI, ACTOR, "2026"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def ids(self, **kwargs):
        return [h.record_id for h in self.fts.search_corpus(**kwargs)]

    def test_scripts_exact_and_folded(self):
        self.assertEqual(self.ids(query=G_POLY), ["r0"])
        self.assertEqual(self.ids(query=G_PLAIN), ["r0"])
        self.assertEqual(self.ids(query=H_POINT), ["r1"])
        self.assertEqual(self.ids(query=H_PLAIN), ["r1"])
        self.assertEqual(self.ids(query=L_ACC), ["r2"])
        self.assertEqual(self.ids(query=L_PLAIN), ["r2"])

    def test_prefix(self):
        self.assertEqual(self.ids(query="\u03bb\u03bf\u03b3", prefix=True), ["r0"])
        self.assertEqual(self.ids(query="\u03bb\u03cc\u03b3", prefix=True), ["r0"])
        self.assertEqual(self.ids(query="\u05d0\u05dc", prefix=True), ["r1"])
        self.assertEqual(self.ids(query="Dee", prefix=True), ["r2"])

    def test_no_romanization(self):
        for query in ("logos", "elohim", "Jesus"):
            self.assertEqual(self.ids(query=query), [], query)

    def test_dedupe_and_modes(self):
        self.assertEqual(len(self.fts.search_corpus(G_PLAIN)), 1)
        self.assertEqual(self.ids(query=G_PLAIN, diacritics="folded"), ["r0"])
        self.assertEqual(self.ids(query=G_POLY, diacritics="exact"), ["r0"])
        with self.assertRaises(SearchError):
            self.fts.search_corpus("x", diacritics="romanized")

    def test_filters(self):
        self.assertEqual(self.ids(query=G_PLAIN, edition_id="e"), ["r0"])
        self.assertEqual(self.ids(query=G_PLAIN, edition_id="nope"), [])
        self.assertEqual(self.ids(query=G_PLAIN, layers=["scripture"]), ["r0"])
        self.assertEqual(self.ids(query=G_PLAIN, layers=["historical_evidence"]), [])

    def test_stored_unchanged(self):
        rows = dict(self.conn.execute("select id, text from corpus_records").fetchall())
        self.assertEqual((rows["r0"], rows["r1"], rows["r2"]), (G_POLY, H_POINT, L_ACC))

    def test_claims_and_flags(self):
        self.fts.index_claim(claim_id="c1", layer="linguistic_observation",
                             statement=G_POLY + " trace")
        hits = self.fts.search_claims(G_PLAIN)
        self.assertEqual([(h.claim_id, h.non_authoritative) for h in hits],
                         [("c1", False)])
        self.assertEqual(self.fts.search_claims(G_PLAIN, exclude_ai_hypothesis=True)
                         [0].claim_id, "c1")
        self.fts.index_claim(claim_id="c2", layer="ai_hypothesis",
                             statement="hypothesis trace")
        flagged = [h for h in self.fts.search_claims("hypothesis")]
        self.assertTrue(all(h.non_authoritative for h in flagged))
        self.assertEqual(self.fts.search_claims("hypothesis", exclude_ai_hypothesis=True), ())
        with self.assertRaises(SearchError):
            self.fts.index_claim(claim_id="c3", layer="ai_hypothesis",
                                 statement="x", non_authoritative=False)

    def test_injection_safe(self):
        self.assertEqual(self.ids(query='" OR 1=1 --'), [])
        with self.assertRaises(SearchError):
            self.fts.search_corpus("")
        with self.assertRaises(SearchError):
            self.fts.search_corpus("x", limit=0)


if __name__ == "__main__":
    unittest.main()


class FtsModesAndPaginationTest(unittest.TestCase):
    """exact/folded/both semantics, byte-exact helper, and the pagination fix:
    layer/edition filters must not drop relevant results because the inner
    LIMIT ran prematurely (directive section 9)."""

    def setUp(self):
        self.conn = connect()
        apply_migrations(self.conn)
        self.fts = FtsIndex(self.conn)
        self.conn.execute(
            "insert into editions(id,key,name,created_at) values ('e','syn','syn','2026')")
        self.conn.execute(
            "insert into canon_profiles(id,key,name,description) values ('p','syn','syn','syn')")
        self.conn.execute(
            "insert into books(id,key,name_en,chapters,testament) values ('b','Syn','Synthetic',1,'ot')")
        self.conn.execute(
            "insert into canonical_references(id,book_id,canon_profile_id,chapter,display)"
            " values ('rf','b','p',1,'Syn 1')")
        # corpus: r0-r2 are 'scripture' matching 'alpha'; r3-r4 are
        # 'historical_evidence' also matching 'alpha' with LOWER rank (more
        # occurrences) so they sort FIRST. A premature inner LIMIT of 2 would
        # fetch only r3/r4 and a 'scripture' filter would then see nothing.
        # a polytonic record for the exact/folded/both mode assertions
        self.fts.index_corpus_record(record_id="r0", layer="scripture",
                                     text=G_POLY, edition_id="e",
                                     reference_display="Syn 1")
        self.conn.execute(
            "insert into corpus_records(id,edition_id,reference_id,text,content_hash,"
            "source_uri,actor,created_at) values (?,?,?,?,?,?,?,?)",
            ("r0", "e", "rf", G_POLY, "sha256:x", "synthetic:test", "test", "2026"))
        for i, (layer, text) in enumerate([
            ("scripture", "alpha alpha alpha"),
            ("scripture", "alpha"),
            ("scripture", "alpha beta"),
            ("historical_evidence", "alpha alpha alpha alpha alpha"),
            ("historical_evidence", "alpha alpha alpha alpha"),
        ]):
            self.fts.index_corpus_record(record_id=f"p{i}", layer=layer,
                                         text=text, edition_id="e",
                                         reference_display="Syn 1")
            self.conn.execute(
                "insert into corpus_records(id,edition_id,reference_id,text,content_hash,"
                "source_uri,actor,created_at) values (?,?,?,?,?,?,?,?)",
                (f"p{i}", "e", "rf", text, "sha256:x", "synthetic:test", "test", "2026"))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_filter_does_not_drop_relevant_results(self):
        # With the old premature inner LIMIT (limit*3=2 for limit=1... more
        # precisely: any inner bound), a scripture-filtered search could return
        # nothing although scripture matches exist. Now all candidates are
        # fetched, then filtered.
        hits = self.fts.search_corpus("alpha", limit=10, layers=["scripture"])
        ids = sorted(h.record_id for h in hits)
        self.assertEqual(ids, ["p0", "p1", "p2"])
        hits2 = self.fts.search_corpus("alpha", limit=1, layers=["scripture"])
        self.assertEqual(len(hits2), 1)  # limit still honoured AFTER filtering
        self.assertEqual(hits2[0].layer, "scripture")
        # edition filter likewise
        hits3 = self.fts.search_corpus("alpha", limit=10, edition_id="e")
        self.assertEqual(len(hits3), 5)
        hits4 = self.fts.search_corpus("alpha", limit=10, edition_id="nope")
        self.assertEqual(hits4, ())

    def test_hits_carry_provenance_and_flags(self):
        hits = self.fts.search_corpus("alpha", limit=10)
        for hit in hits:
            self.assertTrue(hit.layer)
            self.assertFalse(hit.non_authoritative)  # none are ai_hypothesis
            self.assertEqual(hit.source_uri, "synthetic:test")
            self.assertIn("verification_status", hit.to_dict())
        # an ai_hypothesis claim hit is flagged
        self.fts.index_claim(claim_id="c-ai", layer="ai_hypothesis",
                             statement="alpha hypothesis")
        claim_hits = self.fts.search_claims("alpha")
        ai = [h for h in claim_hits if h.claim_id == "c-ai"]
        self.assertTrue(ai and ai[0].non_authoritative)
        self.assertEqual(ai[0].verification_status, None)  # not recorded at this level

    def test_exact_folded_both_modes(self):
        # stored polytonic; exact matches the stored-form column (tokenizer
        # normalization still applies -- NOT byte-exactness, which is what
        # verify_byte_exact provides)
        self.assertEqual(
            [h.record_id for h in self.fts.search_corpus(G_POLY, diacritics="exact")], ["r0"])
        # folded: the accentless query still finds the polytonic record
        self.assertEqual(
            [h.record_id for h in self.fts.search_corpus(G_PLAIN, diacritics="folded")], ["r0"])
        # both: union of both paths, deduplicated (one hit, not two)
        hits = self.fts.search_corpus(G_PLAIN, diacritics="both")
        self.assertEqual([h.record_id for h in hits], ["r0"])
        self.assertEqual(len(hits), 1)

    def test_byte_exact_helper(self):
        from scriptura.search import verify_byte_exact
        from scriptura.core.errors import SearchError
        self.assertTrue(verify_byte_exact("\u03bb\u03cc\u03b3\u03bf\u03c2", "\u03bb\u03cc\u03b3\u03bf\u03c2"))
        self.assertFalse(verify_byte_exact("\u03bb\u03cc\u03b3\u03bf\u03c2", "\u03bb\u03bf\u03b3\u03bf\u03c2"))
        self.assertFalse(verify_byte_exact("logos", "logos "))
        with self.assertRaises(SearchError):
            verify_byte_exact("x", None)
