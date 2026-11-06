"""Documentation integrity: required docs present, relative links resolve."""
from __future__ import annotations
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
ANCHOR_STRIP = re.compile(r"#.*$")


def iter_markdown():
    out = []
    for path in ROOT.rglob("*.md"):
        parts = path.relative_to(ROOT).parts
        if any(p in {".git", ".cline-home", "node_modules", ".venv"} for p in parts):
            continue
        out.append(path)
    return sorted(out)


def check_spec_frontmatter(path, errors):
    text = path.read_text(encoding="utf-8")
    name = path.name
    if name.startswith(("BKB-", "DKF-")):
        for field in ("**ID**", "**Status**", "**Version**", "Change history"):
            if field not in text:
                errors.append("%s: specification missing %s" % (path.relative_to(ROOT), field))
    if name.startswith("ADR-0") and name != "ADR-TEMPLATE.md":
        if "Alternatives considered" not in text:
            errors.append("%s: ADR missing mandatory Alternatives considered" % path.relative_to(ROOT))


def check_links(path, errors):
    text = path.read_text(encoding="utf-8")
    for _, target in LINK_RE.findall(text):
        if target.startswith(SKIP_PREFIXES) or not target.strip():
            continue
        clean = ANCHOR_STRIP.sub("", target)
        if not clean:
            continue
        resolved = (path.parent / clean).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append("%s: link escapes repo: %s" % (path.relative_to(ROOT), target))
            continue
        if not resolved.exists():
            errors.append("%s: broken relative link: %s" % (path.relative_to(ROOT), target))


def main():
    errors = []
    docs = iter_markdown()
    if not docs:
        print("check-docs FAILED: no markdown found")
        return 1
    for path in docs:
        check_spec_frontmatter(path, errors)
        check_links(path, errors)
    # ADR index must list every ADR file
    adr_dir = ROOT / "docs/architecture/ADR"
    adr_files = sorted(p.name for p in adr_dir.glob("ADR-0*.md"))
    index = (adr_dir / "README.md").read_text(encoding="utf-8")
    for name in adr_files:
        if name not in index:
            errors.append("ADR index missing: " + name)
    if errors:
        print("check-docs FAILED:")
        for error in errors:
            print("  - " + error)
        return 1
    print("check-docs PASSED (%d documents)" % len(docs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
