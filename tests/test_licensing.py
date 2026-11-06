"""Licence registry, manifest, and the ten-condition gate. R3: 6, 12."""
import pathlib, unittest
from scriptura.core.errors import LicenceError
from scriptura.provenance import LicensingStore, load_licensing_store, require_ingestible
from scriptura.core.errors import LicenceGateError
ROOT = pathlib.Path(__file__).resolve().parents[1]
REG = ROOT / "docs/data/source-registry.json"
MAN = ROOT / "docs/data/licence-manifest.json"
SCH = ROOT / "schemas"


class RegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = load_licensing_store(REG, MAN, SCH)

    def test_counts(self):
        self.assertEqual(len(self.store._sources), 27)
        self.assertEqual(len(self.store._licences), 9)
        self.assertFalse(self.store.registry_gate_open())
        self.assertEqual(self.store._manifest_datasets(), ())

    def test_consistency(self):
        self.assertEqual(self.store.consistency_problems(), ())

    def test_nothing_ingestible_at_m0(self):
        self.assertEqual(self.store.ingestible_sources(), ())

    def test_verified_sources_refuse_on_gate(self):
        for sid, source in self.store._sources.items():
            if source.get("verification_status") == "verified":
                with self.subTest(sid=sid):
                    result = self.store.evaluate(sid, authorised=[sid])
                    self.assertFalse(result.permitted)
                    codes = [u.split(":")[0] for u in result.unmet]
                    self.assertIn("G9", codes)

    def test_gate_names_every_condition(self):
        result = self.store.evaluate("src-tregelles-gnt")
        codes = sorted(u.split(":")[0] for u in result.unmet)
        for expected in ("G2", "G3", "G4", "G9", "G10"):
            self.assertIn(expected, codes)

    def test_unknown_dataset(self):
        result = self.store.evaluate("src-nope")
        self.assertFalse(result.permitted)
        self.assertTrue(result.unmet[0].startswith("G1"))

    def test_disputed_and_restricted(self):
        for sid in ("src-morphgnt-sblgnt", "src-perseus-hopper", "src-kjv"):
            with self.subTest(sid=sid):
                self.assertFalse(self.store.evaluate(sid, authorised=[sid]).permitted)

    def test_require_raises(self):
        with self.assertRaises(LicenceGateError):
            require_ingestible("src-bsb", authorised=["src-bsb"],
                               registry_path=REG, manifest_path=MAN, schemas_dir=SCH)

    def test_missing_files(self):
        with self.assertRaises(LicenceError):
            load_licensing_store("nope.json", "nope2.json")


if __name__ == "__main__":
    unittest.main()
