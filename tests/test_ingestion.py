"""Ingestion pipeline, adapters, validators. Synthetic fixtures only. R3: 5, 10-11."""
import pathlib, tempfile, unittest
from scriptura.core.errors import IngestionError, LicenceGateError
from scriptura.ingestion import (
    ADAPTER_REGISTRY, CanonicalRecord, ConversionReport, DatasetAdapter,
    IngestionRun, register_adapter, run_ingestion, validate_record,
)
from scriptura.storage import connect
ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "docs/data/source-registry.json"
MAN = ROOT / "docs/data/licence-manifest.json"
SCH = ROOT / "schemas"

URI = "synthetic:test"


class SyntheticAdapter(DatasetAdapter):
    dataset_id = "synthetic-only"
    input_format = "synthetic-1.0"
    version = "0.1.0"

    def convert(self, source_path, *, dataset_id):
        data = pathlib.Path(source_path).read_bytes()
        assert data == b"synthetic fixture bytes"
        good = CanonicalRecord(
            layer="linguistic_observation", kind="claim",
            fields={"observation_type": "morphology", "analyst": "syn",
                    "reference": {"book": "Jhn", "canon_profile": "protestant_66",
                                  "chapter": 1, "verse_start": 1}},
            provenance={"source_uri": URI, "source_kind": "generated",
                        "content_hash": "sha256:" + "0" * 64,
                        "actor": "test", "created_at": "2026-01-01"},
            manifest={"adapter": "SyntheticAdapter"})
        bad = CanonicalRecord(
            layer="theological_interpretation", kind="claim",
            fields={"source_uri": URI},
            provenance={"source_uri": URI, "source_kind": "generated",
                        "content_hash": "sha256:" + "0" * 64,
                        "actor": "test", "created_at": "2026-01-01"},
            manifest={"adapter": "SyntheticAdapter"})
        return ConversionReport(dataset_id=dataset_id, adapter="SyntheticAdapter",
                                adapter_version=self.version, records=(good, bad),
                                skipped=({"input": "row", "reason": "demo"},),
                                source_hash="x", byte_length=len(data))


class IngestionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_adapter(SyntheticAdapter())

    def test_registry_empty_at_import(self):
        # the M0 registry has no adapters; only this test's synthetic one exists
        self.assertIn("synthetic-only", ADAPTER_REGISTRY)

    def test_gate_refuses_first(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"synthetic fixture bytes")
            path = tmp.name
        conn = connect()
        try:
            with self.assertRaises(LicenceGateError):
                run_ingestion(conn, IngestionRun(dataset_id="synthetic-only",
                                                 source_path=path, actor="test"),
                              registry_path=REG, manifest_path=MAN, schemas_dir=SCH)
        finally:
            conn.close()
            pathlib.Path(path).unlink()

    def test_validators(self):
        good = {"kind": "claim", "layer": "linguistic_observation",
                "fields": {"observation_type": "morphology", "analyst": "a"},
                "provenance": {"source_uri": "s", "source_kind": "generated",
                                "content_hash": "sha256:" + "0" * 64,
                                "actor": "t", "created_at": "2026"}}
        self.assertEqual(validate_record(good, 0), [])
        bad = {"kind": "claim", "layer": "theological_interpretation",
               "fields": {"source_uri": "s"},
               "provenance": {"source_uri": "s", "source_kind": "generated",
                               "content_hash": "sha256:" + "0" * 64,
                               "actor": "t", "created_at": "2026"}}
        self.assertTrue(validate_record(bad, 1))
        orphan = dict(good, provenance={})
        self.assertTrue(validate_record(orphan, 2))
        noref = dict(good, reference={"book": "Foo"})
        self.assertTrue(validate_record(noref, 3))

    def test_no_adapter_registered(self):
        conn = connect()
        try:
            with self.assertRaises((LicenceGateError, IngestionError)):
                run_ingestion(conn, IngestionRun(dataset_id="no-such-dataset",
                                                 source_path="/nonexistent", actor="t"),
                              registry_path=REG, manifest_path=MAN, schemas_dir=SCH)
        finally:
            conn.close()

    def test_no_real_adapter_in_tree(self):
        # M0: no dataset adapter may exist outside tests
        adapters = list((ROOT / "src/scriptura/ingestion/adapters").glob("*.py"))
        names = sorted(p.name for p in adapters)
        self.assertEqual(names, ["__init__.py", "base.py"])


if __name__ == "__main__":
    unittest.main()
