"""Repository invariants: no corpus data, no banned artifacts, no deps."""
import ast, pathlib, re, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "scriptura"
FORBIDDEN = {"yaml", "pytest", "fastapi", "starlette", "pydantic", "leann",
             "httpx", "requests", "numpy", "torch", "sqlalchemy", "neo4j"}
PROHIBITED_MODS = {"pickle", "marshal", "ctypes", "subprocess", "socket"}


def repo_files():
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in {".git", ".cline-home", "tmp", "__pycache__"} for p in path.parts):
            continue
        out.append(path)
    return out


class HygieneTest(unittest.TestCase):
    def test_no_corpus_bytes(self):
        bad = [p for p in repo_files()
               if str(p.relative_to(ROOT)).startswith(
                   ("datasets/raw/", "datasets/interim/", "datasets/processed/",
                    "datasets/third_party/")) and p.name != ".gitkeep"
               and p.name != "README.md"]
        self.assertEqual(bad, [], f"corpus bytes present: {bad[:5]}")

    def test_no_databases_or_caches(self):
        bad = [str(p.relative_to(ROOT)) for p in repo_files()
               if p.suffix in (".db", ".sqlite", ".sqlite3", ".pyc")]
        self.assertEqual(bad, [], f"banned artifacts: {bad[:5]}")

    def test_no_third_party_runtime_imports(self):
        offenders = []
        for path in SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            tops = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    tops.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    tops.add(node.module.split(".")[0])
            rel = str(path.relative_to(ROOT))
            for top in sorted(tops & FORBIDDEN):
                allowed = ((top == "leann" and rel.endswith("leann_adapter.py"))
                           or (top == "fastapi" and rel.endswith("fastapi_app.py")))
                if not allowed:
                    offenders.append(f"{rel}: {top}")
        self.assertEqual(offenders, [])

    def test_no_prohibited_runtime(self):
        offenders = []
        for path in SRC.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            tops = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    tops.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    tops.add(node.module.split(".")[0])
            rel = str(path.relative_to(ROOT))
            for top in sorted(tops & PROHIBITED_MODS):
                offenders.append(f"{rel}: {top}")
            if re.search(r"\b(eval|exec)\s*\(", text):
                offenders.append(f"{rel}: eval/exec")
        self.assertEqual(offenders, [])

    def test_no_gomine_runtime(self):
        # A runtime dependency means: an import of gomine, a network call to a
        # Gomine endpoint, or reading Gomine credentials/config. Mentions in
        # docstrings and comments (specification references) are not dependencies.
        offenders = []
        for path in SRC.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    if "gomine" in name.lower():
                        offenders.append(str(path.relative_to(ROOT)) + ": import")
            code = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    continue  # docstrings and string literals are not calls
                if isinstance(node, ast.Call):
                    code.append(ast.dump(node))
            blob = " ".join(code).lower()
            if "gomine" in blob:
                offenders.append(str(path.relative_to(ROOT)) + ": call")
        self.assertEqual(offenders, [])

    def test_no_agent_execution(self):
        bad = [str(p.relative_to(ROOT)) for p in (ROOT / "agents/specs").rglob("*")
               if p.is_file() and p.suffix in (".py", ".sh")]
        self.assertEqual(bad, [])

    def test_no_corpus_in_git(self):
        import subprocess
        tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                                 cwd=str(ROOT)).stdout.splitlines()
        bad = [t for t in tracked
               if t.startswith(("datasets/raw/", "datasets/interim/",
                                "datasets/processed/", "datasets/third_party/"))
               and not t.endswith((".gitkeep", "README.md"))]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
