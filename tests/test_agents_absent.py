"""No autonomous agent execution exists at M0."""
import pathlib, re, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS = [
    (r"\bschedule\b.*\b(cron|every|interval)\b", "scheduling"),
    (r"while\s+True\s*:", "unbounded loop"),
    (r"import\s+(schedule|apscheduler|celery|rq)", "task queue"),
]


class AgentAbsenceTest(unittest.TestCase):
    def test_no_executable_specs(self):
        bad = [str(p.relative_to(ROOT)) for p in (ROOT / "agents/specs").rglob("*")
               if p.is_file() and p.suffix in (".py", ".sh")]
        self.assertEqual(bad, [])

    def test_no_autonomy_patterns(self):
        offenders = []
        for path in (ROOT / "src/scriptura").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern, label in FORBIDDEN_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    offenders.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual(offenders, [])

    def test_no_agent_runtime_imports(self):
        import ast
        offenders = []
        for path in (ROOT / "src/scriptura").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    if name.split(".")[0] in ("schedule", "apscheduler", "celery",
                                                "rq", "dramatiq"):
                        offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
