
"""Read-only stdlib HTTP surface.

Normative source: BKB-ARCH-001 section 8.2; ADR-0004.
Read-only. No write endpoints. Loopback by default.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from ..core.errors import ApiError
from ..graph import KnowledgeGraph, traverse
from ..storage import apply_migrations, connect

__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "ROUTES", "ScripturaHandler",
           "describe_database", "build_router_snapshot", "serve"]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

ROUTES = (
    "GET /health",
    "GET /describe",
    "GET /search?q=...&limit=..&prefix=..&diacritics=..",
    "GET /graph/traverse?node=...&depth=..&direction=..",
    "GET /graph/node?id=...",
)


def _json(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class ScripturaHandler(BaseHTTPRequestHandler):
    """Read-only handler. Any non-GET method is rejected with 405."""

    server_version = "ScripturaM0/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        pass

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # BaseHTTPRequestHandler sets self.server during ITS __init__, so read
        # the db path only after super().__init__ has run. The per-request
        # connection is opened lazily by _db() on first use.
        self._owned_conn: sqlite3.Connection | None = None
        super().__init__(*args, **kwargs)

    def _db(self) -> sqlite3.Connection:
        if self._owned_conn is not None:
            return self._owned_conn
        db_path = getattr(self.server, "db_path", None)
        if db_path is not None:
            # check_same_thread=False is SAFE here because this connection is
            # used only by this handler instance, in this thread, and closed in
            # finish(). It is never shared.
            self._owned_conn = connect(str(db_path), read_only=True)
            return self._owned_conn
        server_owned = getattr(self.server, "db_conn", None)
        if server_owned is not None:
            return server_owned
        raise ApiError("No database connection is available for this request.")

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            owned = getattr(self, "_owned_conn", None)
            if owned is not None:
                try:
                    owned.close()
                except Exception:
                    pass

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        try:
            if parsed.path == "/health":
                _json(self, 200, {"ok": True, "service": "scriptura", "writes": False})
            elif parsed.path == "/describe":
                _json(self, 200, describe_database(self._db()))
            elif parsed.path == "/search":
                _json(self, 200, self._search(params))
            elif parsed.path == "/graph/traverse":
                _json(self, 200, self._traverse(params))
            elif parsed.path == "/graph/node":
                _json(self, 200, self._node(params))
            else:
                _json(self, 404, {"error": "unknown route", "routes": list(ROUTES)})
        except ApiError as exc:
            _json(self, 400, {"error": str(exc)})
        except Exception as exc:
            _json(self, 500, {"error": f"internal error: {exc}"})

    def _reject(self) -> None:
        _json(self, 405, {"error": "read-only surface: only GET is supported"})

    do_POST = _reject  # type: ignore[assignment]
    do_PUT = _reject  # type: ignore[assignment]
    do_PATCH = _reject  # type: ignore[assignment]
    do_DELETE = _reject  # type: ignore[assignment]
    do_OPTIONS = _reject  # type: ignore[assignment]

    def _search(self, params: dict[str, list[str]]) -> Any:
        q = (params.get("q") or [""])[0]
        if not q.strip():
            raise ApiError("Missing required query parameter: q")
        try:
            limit = int((params.get("limit") or ["50"])[0])
        except ValueError:
            raise ApiError("limit must be an integer") from None
        prefix = (params.get("prefix") or ["false"])[0].lower() in ("1", "true", "yes")
        diacritics = (params.get("diacritics") or ["both"])[0]
        from ..search import FtsIndex
        fts = FtsIndex(self._db())
        hits = fts.search_corpus(q, limit=limit, prefix=prefix, diacritics=diacritics)
        return {"query": q, "backend": "fts5",
                "hits": [h.to_dict() for h in hits]}

    def _traverse(self, params: dict[str, list[str]]) -> Any:
        node = (params.get("node") or [""])[0]
        if not node:
            raise ApiError("Missing required query parameter: node")
        try:
            depth = int((params.get("depth") or ["3"])[0])
        except ValueError:
            raise ApiError("depth must be an integer") from None
        direction = (params.get("direction") or ["out"])[0]
        return traverse(KnowledgeGraph(self._db()), node,
                        max_depth=depth, direction=direction).to_dict()

    def _node(self, params: dict[str, list[str]]) -> Any:
        node_id = (params.get("id") or [""])[0]
        if not node_id:
            raise ApiError("Missing required query parameter: id")
        node = KnowledgeGraph(self._db()).get_node(node_id)
        if node is None:
            raise ApiError(f"Unknown node {node_id!r}.")
        return node.to_dict()

"""Read-only stdlib HTTP surface, part 1: handler and routing."""


def describe_database(conn: sqlite3.Connection) -> dict[str, Any]:
    tables = [r[0] for r in conn.execute(
        "select name from sqlite_master where type='table' "
        "and name not like 'sqlite_%' order by name")]
    counts: dict[str, int] = {}
    for table in tables:
        if table == "schema_migrations":
            continue  # governance ledger, not corpus content
        if table.startswith(("corpus_fts", "claim_fts")) and table not in (
            "corpus_fts", "claim_fts"):
            continue
        try:
            counts[table] = int(conn.execute(f'select count(*) from "{table}"').fetchone()[0])
        except sqlite3.Error:
            counts[table] = -1
    from ..storage import schema_version
    try:
        version = schema_version(conn)
    except Exception:
        version = 0
    return {"service": "scriptura", "writes": False, "tables": tables,
            "counts": counts, "schema_version": version,
            "routes": list(ROUTES)}


def build_router_snapshot(db_path: str) -> dict[str, Any]:
    with connect(db_path, read_only=True) as conn:
        return describe_database(conn)


def serve(db_path: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    path = str(db_path)

    server = ThreadingHTTPServer((host, port), ScripturaHandler)
    server.db_path = path  # type: ignore[attr-defined]
    print(f"Scriptura read-only API on http://{host}:{port} (db: {path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scriptura read-only API (stdlib).")
    parser.add_argument("--db", required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    if args.describe:
        print(json.dumps(build_router_snapshot(args.db), indent=2, ensure_ascii=False))
    else:
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            print("WARNING: binding beyond loopback requires an ADR on auth.")
        serve(args.db, args.host, args.port)

