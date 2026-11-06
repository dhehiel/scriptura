"""Repository structure and hygiene checks (make check entry point)."""
from __future__ import annotations
import ast, json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "scriptura"
REQUIRED_FILES = [
    "LICENSE", "NOTICE", "README.md", "AGENTS.md", "CONTRIBUTING.md",
    "SECURITY.md", "GOVERNANCE.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md",
    "M0-IMPLEMENTATION-REPORT.md",
    "pyproject.toml", "Makefile", ".gitignore", ".editorconfig",
    ".clinerules/README.md",
    ".clinerules/000-project-governance.md",
    ".clinerules/010-source-integrity.md",
    ".clinerules/020-epistemic-layers.md",
    ".clinerules/030-research-standards.md",
    ".clinerules/040-engineering.md",
    ".clinerules/050-data-licensing.md",
    ".clinerules/060-agent-safety.md",
    ".clinerules/070-decision-log-protocol.md",
    "docs/architecture/README.md",
    "docs/architecture/BKB-ARCH-001-system-architecture.md",
    "docs/architecture/BKB-DATA-001-data-model.md",
    "docs/architecture/BKB-CORPUS-001-corpus-ingestion.md",
    "docs/architecture/BKB-AGENTS-001-agent-framework.md",
    "docs/architecture/BKB-VERIFY-001-verification-framework.md",
    "docs/architecture/DKF-ARCH-001-discovery-framework.md",
    "docs/architecture/ADR/README.md",
    "docs/architecture/ADR/ADR-TEMPLATE.md",
    "docs/data/README.md",
    "docs/data/source-registry.json",
    "docs/data/licence-manifest.json",
    "docs/data/attribution/ATTRIBUTIONS.md",
    "docs/milestones/README.md",
    "docs/milestones/M0-acceptance-criteria.md",
    "docs/milestones/ROADMAP.md",
    "docs/operations/README.md",
    "docs/research/README.md",
    "docs/research/methodology.md",
    "schemas/README.md",
]
REQUIRED_DIRS = [
    "docs/architecture/ADR", "docs/data/attribution", "docs/milestones",
    "docs/operations", "docs/research", "datasets/raw", "datasets/interim",
    "datasets/processed", "datasets/manifests", "datasets/third_party",
    "schemas/core", "schemas/data", "schemas/agents", "schemas/verification",
    "src/scriptura/core", "src/scriptura/storage", "src/scriptura/graph",
    "src/scriptura/search", "src/scriptura/retrieval", "src/scriptura/ingestion",
    "src/scriptura/provenance", "src/scriptura/schemas", "src/scriptura/api",
    "agents/specs", "agents/runs", "agents/prompts", "evaluation/benchmarks",
    "evaluation/datasets", "evaluation/reports", "tests", "tools",
]
BANNED_SUFFIXES = (".db", ".db-journal", ".db-wal", ".db-shm", ".sqlite",
                   ".sqlite3", ".pyc", ".pyo", ".egg-info")
BANNED_NAMES = {".DS_Store", "Thumbs.db"}
FORBIDDEN_TOP_LEVELS = {
    "yaml", "pytest", "fastapi", "starlette", "pydantic", "leann", "httpx",
    "requests", "numpy", "pandas", "torch", "tensorflow", "sklearn",
    "sqlalchemy", "flask", "django", "celery", "redis", "neo4j",
    "networkx", "rdflib",
}
PROHIBITED_IMPORTS = {"pickle", "marshal", "ctypes", "subprocess", "socket",
                      "urllib.request", "urllib3", "http.client"}
PROHIBITED_NAMES = re.compile(r"\b(eval|exec)\s*\(")
PRUNE_DIRS = {".git", ".cline-home", "tmp", "__pycache__", ".venv", "venv",
              "node_modules", ".pytest_cache", "htmlcov"}

def iter_repo_files():
    out = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in PRUNE_DIRS for part in path.relative_to(ROOT).parts):
            continue
        out.append(path)
    return out


def check_required(errors):
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append("missing required file: " + rel)
    for rel in REQUIRED_DIRS:
        if not (ROOT / rel).is_dir():
            errors.append("missing required directory: " + rel)


def check_banned_artifacts(files, errors):
    for path in files:
        rel = str(path.relative_to(ROOT))
        if path.suffix in BANNED_SUFFIXES or path.name in BANNED_NAMES:
            errors.append("banned artifact present: " + rel)
        for zone in ("datasets/raw/", "datasets/interim/", "datasets/processed/",
                     "datasets/third_party/"):
            if rel.startswith(zone) and path.name not in (".gitkeep", "README.md"):
                if zone == "datasets/third_party/":
                    errors.append("vendored data (requires licence review): " + rel)
                else:
                    errors.append("corpus bytes in landing zone: " + rel)


def _top_level_imports(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
    return found


def check_dependency_hygiene(errors):
    for path in sorted(SRC.rglob("*.py")):
        rel = str(path.relative_to(ROOT))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(rel + ": syntax error: " + str(exc))
            continue
        for top in sorted(_top_level_imports(tree) & FORBIDDEN_TOP_LEVELS):
            allowed = ((top == "leann" and rel.endswith("retrieval/leann_adapter.py"))
                       or (top == "fastapi" and rel.endswith("api/fastapi_app.py")))
            if not allowed:
                errors.append(rel + ": forbidden third-party import: " + top)
        for top in sorted(_top_level_imports(tree) & PROHIBITED_IMPORTS):
            errors.append(rel + ": prohibited import: " + top)
        text = path.read_text(encoding="utf-8")
        if PROHIBITED_NAMES.search(text):
            errors.append(rel + ": prohibited eval/exec use")
        # NOTE: Gomine mentions in docstrings/comments are specification
        # references, not runtime dependencies. Runtime Gomine coupling is
        # enforced on imports above and on call sites by
        # tests/test_repo_hygiene.py::test_no_gomine_runtime, so a prose scan
        # here would only produce false positives.


def check_compiles_and_parses(files, errors):
    for path in files:
        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                errors.append(str(path.relative_to(ROOT)) + ": syntax error: " + str(exc))
        elif path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(str(path.relative_to(ROOT)) + ": invalid JSON: " + str(exc))


def check_no_agent_execution(errors):
    for path in (ROOT / "agents" / "specs").rglob("*"):
        if path.is_file() and path.suffix in (".py", ".sh"):
            errors.append("executable agent code: " + str(path.relative_to(ROOT)))


def run_subcheck(name, errors):
    script = ROOT / "tools" / name
    try:
        proc = subprocess.run([sys.executable, str(script)], capture_output=True,
                              text=True, cwd=str(ROOT))
    except Exception as exc:
        errors.append(name + ": could not run: " + str(exc))
        return
    if proc.returncode != 0:
        errors.append(name + " FAILED:\n" + proc.stdout + "\n" + proc.stderr)


def main():
    errors = []
    files = iter_repo_files()
    check_required(errors)
    check_banned_artifacts(files, errors)
    check_dependency_hygiene(errors)
    check_compiles_and_parses(files, errors)
    check_no_agent_execution(errors)
    for sub in ("check_licences.py", "check_docs.py", "check_schemas.py"):
        run_subcheck(sub, errors)
    if errors:
        print("make check FAILED:")
        for error in errors:
            print("  - " + error)
        return 1
    print("make check PASSED (%d files scanned)" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
