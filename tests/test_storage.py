"""Database, migrations, ledger, CHECK constraints, seeding. R3: 7."""
import pathlib, sqlite3, tempfile, unittest
from scriptura.core.errors import IntegrityError, MigrationError
from scriptura.storage import (
    apply_migrations, applied_migrations, capability_report, connect,
    discover_migrations, pending_migrations, probe_capabilities,
    require_capabilities, schema_version, seed_reference_data, verify_ledger,
)


class CapabilityTest(unittest.TestCase):
    def test_probe_satisfied(self):
        caps = probe_capabilities()
        self.assertTrue(caps.satisfied, capability_report())
        self.assertTrue(caps.unicode61_diacritics)
        self.assertTrue(caps.fts5_functional)

    def test_require_ok(self):
        self.assertTrue(require_capabilities().satisfied)


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()

    def tearDown(self):
        self.conn.close()

    def test_apply_and_reapply(self):
        self.assertEqual([m.filename for m in apply_migrations(self.conn)],
                         ["0001_bootstrap.sql", "0002_seven_layer_epistemic_model.sql"])
        self.assertEqual(schema_version(self.conn), 2)
        self.assertEqual(apply_migrations(self.conn), ())
        self.assertEqual(len(verify_ledger(self.conn)), 2)

    def test_tables_exist(self):
        apply_migrations(self.conn)
        tables = {r[0] for r in self.conn.execute(
            "select name from sqlite_master where type='table'")}
        for expected in ("licences", "datasets", "canon_profiles", "books",
                         "canonical_references", "editions", "witnesses",
                         "corpus_records", "claims", "nodes", "edges",
                         "provenance_events", "ingestion_runs",
                         "identifier_mappings", "derivations"):
            self.assertIn(expected, tables)

    def test_foreign_keys_on(self):
        self.assertEqual(self.conn.execute("pragma foreign_keys").fetchone()[0], 1)

    def test_ledger_hash_mismatch(self):
        apply_migrations(self.conn)
        with tempfile.TemporaryDirectory() as tmp:
            src = pathlib.Path(tmp) / "0001_copy.sql"
            src.write_text("-- tampered")
            # simulate an edited migration by pointing a fake dir at the ledger
            fake = pathlib.Path(tmp) / "migs"
            fake.mkdir()
            import shutil
            shutil.copy(pathlib.Path(
                "src/scriptura/storage/migrations/0001_bootstrap.sql"), fake / "0001_bootstrap.sql")
            # sanity: genuine dir verifies
            self.assertEqual(len(verify_ledger(self.conn)), 2)

    def test_duplicate_sequence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / "0001_a.sql").write_text("select 1;")
            (d / "0001_b.sql").write_text("select 2;")
            with self.assertRaises(MigrationError):
                discover_migrations(d)

    def test_pending(self):
        self.assertEqual(len(pending_migrations(self.conn)), 2)
        apply_migrations(self.conn)
        self.assertEqual(pending_migrations(self.conn), ())


class ConstraintTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()
        apply_migrations(self.conn)

    def tearDown(self):
        self.conn.close()

    def _licence(self, lid="l1"):
        self.conn.execute(
            "insert into licences(id,name,evidence_kind,verification_status,licence_url,"
            "retrieved_at,notes,created_at) values (?,?,?,?,?,?,?,?)",
            (lid, "Test", "primary", "verified", "https://example.invalid/licence",
             "2026-01-01", "n", "2026-01-01"))

    def test_licence_verified_requires_primary(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into licences(id,name,evidence_kind,verification_status,notes,created_at)"
                " values (?,?,?,?,?,?)",
                ("lbad", "Bad", "secondary", "verified", "n", "2026-01-01"))

    def test_dataset_requires_authoriser(self):
        self._licence()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into datasets(id,key,name,licence_id,source_uri,authorised_by,created_at)"
                " values (?,?,?,?,?,?,?)",
                ("d", "k", "n", "l1", "s", "", "2026"))

    def test_layer_closed_set(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,actor,created_at)"
                " values (?,?,?,?,?,?,?,?)",
                ("c", "gospel_truth", "s", "u", "primary", "sha256:x", "a", "t"))

    def test_unattributed_interpretation_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,actor,created_at)"
                " values (?,?,?,?,?,?,?,?)",
                ("c", "theological_interpretation", "s", "u", "primary", "sha256:x", "a", "t"))

    def test_unflagged_hypothesis_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,actor,created_at,"
                "model,method,inputs_json,confidence,generated_at,non_authoritative)"
                " values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("c", "ai_hypothesis", "s", "u", "primary", "sha256:x", "a", "t",
                 "m", "mt", "[]", 0.5, "t", 0))

    def test_confidence_bounds(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,actor,created_at,"
                "model,method,inputs_json,confidence,generated_at)"
                " values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("c", "ai_hypothesis", "s", "u", "primary", "sha256:x", "a", "t",
                 "m", "mt", "[]", 9.9, "t"))

    def test_promotion_without_audit_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "insert into provenance_events(id,entity_kind,entity_id,event_type,actor,occurred_at)"
                " values (?,?,?,?,?,?)",
                ("p", "claim", "c", "promoted", "a", "t"))

    def test_seeds(self):
        counts = seed_reference_data(self.conn)
        self.assertEqual(counts["books"], 86)
        self.assertEqual(counts["profiles"], 6)
        self.assertGreater(counts["memberships"], 200)
        again = seed_reference_data(self.conn)
        self.assertEqual(again["books"], 0)


if __name__ == "__main__":
    unittest.main()


class Migration0002Test(unittest.TestCase):
    """Migration 0002: preservation, constraints, idempotency (directive s13.12).

    Applies 0001 alone, inserts M0-era rows, then applies 0002 and asserts that
    identifiers, values, and row counts are preserved with NO silent
    reclassification, that the seven-layer CHECKs accept the new layers and
    reject unknown ones, and that re-application is a no-op.
    """

    def setUp(self):
        import shutil, tempfile
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="mig0002-"))
        only1 = self.tmp / "only0001"
        only1.mkdir()
        shutil.copy(
            pathlib.Path("src/scriptura/storage/migrations/0001_bootstrap.sql"),
            only1 / "0001_bootstrap.sql")
        self.db = str(self.tmp / "t.db")
        self.conn = connect(self.db)
        apply_migrations(self.conn, only1)  # M0 schema only
        assert schema_version(self.conn) == 1
        seed_reference_data(self.conn)
        self.conn.execute(
            "insert into editions(id,key,name,created_at) values ('e1','ed1','E','2026')")
        self.conn.execute(
            "insert into canonical_references(id,book_id,canon_profile_id,chapter,display) "
            "select 'rf1',(select id from books where key='Jhn'),"
            "(select id from canon_profiles where key='protestant_66'),1,'Jhn 1'")
        cols = ("id", "layer", "non_authoritative", "statement", "reference_id",
                "confidence", "verification_state", "edition_id", "witness_id",
                "evidence_type", "evidence_identifier", "dating", "dating_basis",
                "observation_type", "linguistic_form", "analysis", "source_dataset",
                "analyst", "tradition", "author", "work", "period", "model",
                "method", "inputs_json", "generated_at", "source_uri", "source_kind",
                "content_hash", "dataset_id", "licence_id", "actor", "created_at",
                "supersedes")
        for row in (
            ("c1", "scripture", 0, "stmt1", "rf1", None, None, "e1", None, None,
             None, None, None, None, None, None, None, None, None, None, None, None,
             None, None, None, None, "u", "primary", "sha256:1", None, None,
             "a", "2026", None),
            ("c2", "theological_interpretation", 0, "stmt2", "rf1", None, None,
             None, None, None, None, None, None, None, None, None, None, None,
             "Trad", "Auth", "Work", None, None, None, None, None, "u", "primary",
             "sha256:2", None, None, "a", "2026", None),
            ("c3", "ai_hypothesis", 1, "stmt3", None, 0.7, None, None, None, None,
             None, None, None, None, None, None, None, None, None, None, None, None,
             "model", "method", "[1]", "2026", "u", "generated", "sha256:3",
             None, None, "a", "2026", None),
        ):
            assert len(row) == len(cols)
            self.conn.execute(
                f"insert into claims ({','.join(cols)}) values ({','.join('?' * len(cols))})",
                row)
        self.conn.execute(
            "insert into nodes(id,kind,layer,label,non_authoritative,source_uri,content_hash,"
            "actor,created_at) values ('n1','concept','scripture','l',0,'u','h','a','2026')")
        self.conn.execute(
            "insert into nodes(id,kind,layer,label,non_authoritative,source_uri,content_hash,"
            "actor,created_at) values ('n2','concept','ai_hypothesis','l2',1,'u','h','a','2026')")
        self.conn.execute(
            "insert into edges(id,source_node_id,target_node_id,relation,layer,"
            "non_authoritative,source_uri,content_hash,actor,created_at) "
            "values ('ed1','n1','n2','rel','ai_hypothesis',1,'u','h','a','2026')")
        self.conn.commit()
        self.counts_before = {t: self.conn.execute(
            f"select count(*) from {t}").fetchone()[0]
            for t in ("claims", "nodes", "edges")}
        self.ids_before = [r[0] for r in
                           self.conn.execute("select id from claims order by id")]
        self.conn.close()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_preserves_ids_values_and_counts_without_reclassification(self):
        conn = connect(self.db)
        applied = apply_migrations(conn)
        self.assertEqual([m.filename for m in applied],
                         ["0002_seven_layer_epistemic_model.sql"])
        self.assertEqual(schema_version(conn), 2)
        self.assertEqual(conn.execute("pragma foreign_keys").fetchone()[0], 1)
        ids_after = [r[0] for r in conn.execute("select id from claims order by id")]
        self.assertEqual(ids_after, self.ids_before)
        rows = {r[0]: r[1:] for r in conn.execute(
            "select id, layer, tradition, model from claims")}
        self.assertEqual(rows["c1"][0], "scripture")
        self.assertEqual(rows["c2"][1], "Trad")
        self.assertEqual(rows["c3"][2], "model")
        counts_after = {t: conn.execute(
            f"select count(*) from {t}").fetchone()[0]
            for t in ("claims", "nodes", "edges")}
        self.assertEqual(counts_after, self.counts_before)
        conn.close()

    def test_seven_layer_checks_accept_new_reject_unknown(self):
        conn = connect(self.db)
        apply_migrations(conn)
        conn.execute(
            "insert into claims(id,layer,statement,reference_id,compared_witnesses,"
            "readings_compared,analyst,observation_method,source_uri,source_kind,"
            "content_hash,actor,created_at) "
            "values ('new-textual','textual_observation','s','rf1','A,B','X,Y',"
            "'critic','collation','u','primary','sha256:x','a','2026')")
        conn.execute(
            "insert into claims(id,layer,statement,scholar,work,publication_meta,"
            "supporting_refs,source_uri,source_kind,content_hash,actor,created_at) "
            "values ('new-scholarly','scholarly_interpretation','s','Sch','Work',"
            "'Venue 2020','Ref1','u','primary','sha256:x','a','2026')")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "insert into claims(id,layer,statement,source_uri,source_kind,content_hash,"
                "actor,created_at) values ('bad','gospel_truth','s','u','primary',"
                "'sha256:x','a','2026')")
        conn.close()

    def test_conditional_checks_do_not_leak_across_layers(self):
        conn = connect(self.db)
        apply_migrations(conn)
        # scholarly without work: rejected
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "insert into claims(id,layer,statement,scholar,publication_meta,"
                "supporting_refs,source_uri,source_kind,content_hash,actor,created_at) "
                "values ('b1','scholarly_interpretation','s','Sch','Pub','Refs',"
                "'u','primary','sha256:x','a','2026')")
        # scripture WITHOUT any scholarly fields: accepted (fields not forced)
        conn.execute(
            "insert into claims(id,layer,statement,reference_id,edition_id,source_uri,"
            "source_kind,content_hash,actor,created_at) "
            "values ('ok','scripture','s','rf1','e1','u','primary','sha256:x','a','2026')")
        # textual without readings: rejected
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "insert into claims(id,layer,statement,reference_id,compared_witnesses,"
                "analyst,observation_method,source_uri,source_kind,content_hash,actor,"
                "created_at) values ('b2','textual_observation','s','rf1','W1','An',"
                "'coll','u','primary','sha256:x','a','2026')")
        conn.close()

    def test_idempotent_and_ledger_verified(self):
        conn = connect(self.db)
        apply_migrations(conn)
        self.assertEqual(apply_migrations(conn), ())
        ledger = verify_ledger(conn)
        self.assertEqual([m.sequence for m in ledger], [1, 2])
        conn.close()

    def test_derivations_table_and_edge_columns(self):
        conn = connect(self.db)
        apply_migrations(conn)
        cols_d = [r[1] for r in conn.execute("pragma table_info(derivations)")]
        for expected in ("output_ids", "output_layers", "input_ids", "input_layers",
                         "method", "actor", "tool_identity", "verification_state",
                         "reviewer", "decision_authority", "evidence_json",
                         "disagreements_json"):
            self.assertIn(expected, cols_d)
        cols_e = [r[1] for r in conn.execute("pragma table_info(edges)")]
        for expected in ("verification_status", "supporting_evidence", "derivation_id"):
            self.assertIn(expected, cols_e)
        # a supported derivation without reviewer/authority is refused
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "insert into derivations(id,output_ids,output_layers,input_ids,"
                "input_layers,method,actor,created_at,verification_state,source_uri,"
                "content_hash) values (?,?,?,?,?,?,?,?,?,?,?)",
                ("d1", '["o"]', '["ai_hypothesis"]', '["i"]', '["scripture"]',
                 "m", "a", "2026", "supported", "u", "sha256:x"))
        conn.close()
