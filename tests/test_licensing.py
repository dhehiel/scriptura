"""Licence registry, manifest, and the ten-condition gate. R3: 6, 12."""
import json, pathlib, unittest
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


class MultiLicenceTest(unittest.TestCase):
    """A dataset must not pass the gate if ANY applicable licence is unresolved
    or incompatible (BKB-CORPUS-001 4.2; directive section 11)."""

    REGISTRY = {
        "sources": [{
            "source_id": "src-layered", "name": "Layered", "category": "morphology",
            "availability": "open_download", "licence": "CC BY 4.0",
            "licence_url": "https://rights.invalid/x", "retrieved_at": "2026-11-06",
            "evidence_kind": "primary", "verification_status": "verified",
            "ingestible": False, "licence_cleared": True,
            "licensing_model": "layered", "notes": "text + annotation",
        }],
        "ingestion_gate_open": True,
    }
    MANIFEST_OK = {
        "licences": [
            {"licence_id": "lic-text", "applies_to": ["src-layered"],
             "licence": "CC BY 4.0", "verification_status": "verified",
             "evidence_kind": "primary", "licence_url": "https://rights.invalid/t",
             "retrieved_at": "2026-11-06", "derivatives_permitted": True,
             "commercial_use_permitted": True, "share_alike": False,
             "attribution_required": False, "notes": "text"},
            {"licence_id": "lic-annot", "applies_to": ["src-layered"],
             "licence": "CC BY-SA 4.0", "verification_status": "verified",
             "evidence_kind": "primary", "licence_url": "https://rights.invalid/a",
             "retrieved_at": "2026-11-06", "derivatives_permitted": True,
             "commercial_use_permitted": False, "share_alike": True,
             "share_alike_consequence": "derivatives inherit CC BY-SA 4.0",
             "attribution_required": True, "attribution_text": "Credit A",
             "notes": "annotation"},
        ],
        "datasets": [],
    }

    def _store(self, manifest):
        from scriptura.provenance import LicensingStore
        return LicensingStore(dict(self.REGISTRY), manifest, "schemas")

    def test_one_unresolved_licence_blocks_dataset(self):
        manifest = json.loads(json.dumps(self.MANIFEST_OK))
        manifest["licences"][1].update({
            "licence": None, "verification_status": "unverified",
            "evidence_kind": "none", "licence_url": None, "retrieved_at": None,
            "derivatives_permitted": None, "commercial_use_permitted": None,
            "share_alike": None, "share_alike_consequence": None,
            "attribution_required": False, "attribution_text": None,
        })
        result = self._store(manifest).evaluate(
            "src-layered", authorised=["src-layered"])
        self.assertFalse(result.permitted)
        self.assertTrue(any("lic-annot" in u for u in result.unmet),
                        "the refusal must NAME the unresolved licence")

    def test_both_resolved_permits_with_aggregate_restrictions(self):
        result = self._store(self.MANIFEST_OK).evaluate(
            "src-layered", authorised=["src-layered"])
        self.assertTrue(result.permitted)
        # most-restrictive commercial wins: annotation is non-commercial
        self.assertFalse(result.commercial_use_permitted)
        self.assertTrue(result.share_alike)
        self.assertEqual(result.attribution_text, "Credit A")
        self.assertTrue(any("QUARANTINE" in w for w in result.warnings))
        self.assertTrue(any("SHARE-ALIKE" in w for w in result.warnings))

    def test_no_licences_recorded_blocks(self):
        manifest = {"licences": [], "datasets": []}
        result = self._store(manifest).evaluate(
            "src-layered", authorised=["src-layered"])
        self.assertFalse(result.permitted)
        self.assertTrue(any(u.startswith("G2") for u in result.unmet))
