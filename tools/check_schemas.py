"""Schema validity + registry conformance (make check-schemas)."""
from __future__ import annotations
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scriptura.schemas import Validator, load_schema
ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    errors = []
    schemas = sorted((ROOT / "schemas").rglob("*.schema.json"))
    if not schemas:
        print("check-schemas FAILED: no schemas found")
        return 1
    validators = {}
    for schema_path in schemas:
        try:
            validators[schema_path] = Validator(load_schema(schema_path),
                                                schema_path.parent)
        except Exception as exc:
            errors.append("%s: %s" % (schema_path.relative_to(ROOT), exc))
    registry = json.loads((ROOT / "docs/data/source-registry.json").read_text())
    manifest = json.loads((ROOT / "docs/data/licence-manifest.json").read_text())
    entry_v = validators.get(ROOT / "schemas/data/source-registry-entry.schema.json")
    lic_v = validators.get(ROOT / "schemas/data/licence-record.schema.json")
    if entry_v is None or lic_v is None:
        errors.append("data schemas missing from validated set")
    else:
        for source in registry.get("sources", []):
            for v in entry_v.validate(source):
                errors.append("source %s: %s" % (source.get("source_id"), v))
        for lic in manifest.get("licences", []):
            for v in lic_v.validate(lic):
                errors.append("licence %s: %s" % (lic.get("licence_id"), v))
        for dataset in manifest.get("datasets", []):
            man_v = validators.get(ROOT / "schemas/data/dataset-manifest.schema.json")
            if man_v:
                for v in man_v.validate(dataset):
                    errors.append("dataset manifest: %s" % v)
    if errors:
        print("check-schemas FAILED:")
        for error in errors:
            print("  - " + error)
        return 1
    print("check-schemas PASSED (%d schemas, %d sources, %d licences)"
          % (len(schemas), len(registry.get("sources", [])),
             len(manifest.get("licences", []))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
