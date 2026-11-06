"""Build an empty Scriptura knowledge base: apply migrations, report version."""
from __future__ import annotations
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scriptura.storage import apply_migrations, capability_report, connect, schema_version


def main():
    parser = argparse.ArgumentParser(description="Build an empty knowledge base.")
    parser.add_argument("--db", required=True, help="Database file to create.")
    parser.add_argument("--journal", default="WAL")
    parser.add_argument("--seeds", action="store_true",
                        help="Seed the book registry and canon profiles (reference data, not corpus).")
    args = parser.parse_args()
    print(capability_report())
    path = pathlib.Path(args.db)
    if path.exists():
        print("refusing: %s already exists (never overwrite a database)" % path)
        return 1
    conn = connect(str(path), journal=args.journal)
    applied = apply_migrations(conn)
    if args.seeds:
        from scriptura.storage import seed_reference_data
        seed_reference_data(conn)
    conn.commit()
    print("applied: %s" % [m.filename for m in applied])
    print("schema version: %d" % schema_version(conn))
    from scriptura.api.server import describe_database
    counts = describe_database(conn)["counts"]
    print("corpus_records: %d | claims: %d | nodes: %d | edges: %d"
          % (counts.get("corpus_records", -1), counts.get("claims", -1),
             counts.get("nodes", -1), counts.get("edges", -1)))
    conn.close()
    print("database ready: %s (NO corpus data: empty by design at M0)" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
