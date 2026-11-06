"""Module dependency direction: core <- schemas/storage <- ... ; api last."""
import ast, pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "scriptura"
# allowed intra-package imports per module (BKB-ARCH-001 section 4.2)
ALLOWED = {
    "core": set(),
    "schemas": {"core"},
    "storage": {"core"},
    "provenance": {"core", "schemas"},
    "graph": {"core", "storage"},
    "search": {"core", "storage"},
    "retrieval": {"core", "search"},
    "ingestion": {"core", "schemas", "storage", "provenance"},
    "api": {"core", "schemas", "storage", "provenance", "graph", "search",
              "retrieval", "ingestion"},
}


class BoundaryTest(unittest.TestCase):
    def test_import_direction(self):
        offenders = []
        for path in SRC.rglob("*.py"):
            module = path.relative_to(SRC).parts[0]
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                target = None
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.startswith("scriptura."):
                            target = a.name.split(".")[1]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("scriptura."):
                        target = node.module.split(".")[1]
                    elif node.module == "scriptura":
                        target = None
                    elif node.level and len(path.relative_to(SRC).parts) > 1:
                        target = path.relative_to(SRC).parts[0]
                if target and target != module and target not in ALLOWED.get(module, set()):
                    offenders.append(f"{path.relative_to(ROOT)}: {module} -> {target}")
        # relative imports within the same module are fine; only flag cross-module
        self.assertEqual(offenders, [], "inward dependency violation")

    def test_core_has_no_io(self):
        import re
        offenders = []
        for path in (SRC / "core").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in ("sqlite3", "urllib", "http.client", "socket", "open("):
                if token in text and "hashlib" not in text[:0]:
                    if token == "open(" and "open(" in text:
                        offenders.append(f"{path.relative_to(ROOT)}: {token}")
                    elif token != "open(":
                        offenders.append(f"{path.relative_to(ROOT)}: {token}")
        # filter: error messages may mention these words; check imports instead
        offenders = [o for o in offenders if "import" in
                     (SRC / "/".join(o.split(":")[0].split("/")[-1:])).__str__() or True]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
