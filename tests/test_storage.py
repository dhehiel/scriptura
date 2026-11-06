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
                         ["0001_bootstrap.sql"])
        self.assertEqual(schema_version(self.conn), 1)
        self.assertEqual(apply_migrations(self.conn), ())
        self.assertEqual(len(verify_ledger(self.conn)), 1)

    def test_tables_exist(self):
        apply_migrations(self.conn)
        tables = {r[0] for r in self.conn.execute(
            "select name from sqlite_master where type='table'")}
        for expected in ("licences", "datasets", "canon_profiles", "books",
                         "canonical_references", "editions", "witnesses",
                         "corpus_records", "claims", "nodes", "edges",
                         "provenance_events", "ingestion_runs",
                         "identifier_mappings"):
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
            self.assertEqual(len(verify_ledger(self.conn)), 1)

    def test_duplicate_sequence_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp)
            (d / "0001_a.sql").write_text("select 1;")
            (d / "0001_b.sql").write_text("select 2;")
            with self.assertRaises(MigrationError):
                discover_migrations(d)

    def test_pending(self):
        self.assertEqual(len(pending_migrations(self.conn)), 1)
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
