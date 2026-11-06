"""JSON Schema documents, subset validator, registry conformance."""
import json, pathlib, unittest
from scriptura.core.errors import UnsupportedSchemaKeywordError
from scriptura.schemas import Validator, check_schema_supported, load_schema
ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


class SchemaTest(unittest.TestCase):
    def test_all_schemas_supported(self):
        files = sorted(SCHEMAS.rglob("*.schema.json"))
        self.assertGreaterEqual(len(files), 12)
        for path in files:
            with self.subTest(schema=path.name):
                load_schema(path)

    def test_unsupported_keyword_raises(self):
        with self.assertRaises(UnsupportedSchemaKeywordError):
            Validator({"type": "object", "anyOf": [{"type": "string"}]})
        with self.assertRaises(UnsupportedSchemaKeywordError):
            check_schema_supported({"$defs": {"a": {"type": "string"}}}, "x")

    def test_registries_conform(self):
        registry = json.loads((ROOT / "docs/data/source-registry.json").read_text())
        manifest = json.loads((ROOT / "docs/data/licence-manifest.json").read_text())
        entry_v = Validator(load_schema(SCHEMAS / "data/source-registry-entry.schema.json"),
                            SCHEMAS / "data")
        lic_v = Validator(load_schema(SCHEMAS / "data/licence-record.schema.json"),
                          SCHEMAS / "data")
        bad = [s["source_id"] for s in registry["sources"] if entry_v.validate(s)]
        self.assertEqual(bad, [])
        bad = [lic["licence_id"] for lic in manifest["licences"] if lic_v.validate(lic)]
        self.assertEqual(bad, [])
        self.assertEqual(manifest["datasets"], [])

    def test_ref_resolution(self):
        claim_schema = load_schema(SCHEMAS / "core/claim.schema.json")
        validator = Validator(claim_schema, SCHEMAS / "core")
        doc = {"id": "x", "layer": "ai_hypothesis", "non_authoritative": True,
               "statement": "s",
               "provenance": {"source_uri": "u", "source_kind": "generated",
                               "content_hash": "sha256:" + "0" * 64,
                               "actor": "a", "created_at": "t"}}
        self.assertEqual(validator.validate(doc), ())
        bad = dict(doc, layer="nope")
        self.assertTrue(validator.validate(bad))

    def test_validator_types(self):
        validator = Validator({"type": ["integer", "null"]})
        self.assertEqual(validator.validate(3), ())
        self.assertEqual(validator.validate(None), ())
        self.assertTrue(validator.validate("x"))
        validator = Validator({"type": "integer"})
        self.assertEqual(validator.validate(3.0), ())  # integral float per JSON Schema
        self.assertTrue(validator.validate(True))  # bool is not integer


if __name__ == "__main__":
    unittest.main()
