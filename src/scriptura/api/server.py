
"""Read-only stdlib HTTP surface.

Normative source: BKB-ARCH-001 section 8.2 (corrected); ADR-0004; ADR-0011.

Read-only. No write endpoints. **Loopback only: a non-loopback binding is
REJECTED BY DEFAULT** (directive section 10). A read-only API is not
automatically safe for public exposure. An override flag does NOT independently
authorize public exposure: external binding requires ALL FOUR of

1. an explicit ``allow_non_loopback`` operator flag,
2. an explicit security configuration,
3. a documented authentication and authorization design,
4. an explicit operator acknowledgement,

PLUS a listed approved external-binding ADR. No such ADR exists yet, so
external binding is refused unconditionally today; the gate fails closed rather
than opening an insecure surface to satisfy a configuration option.
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

__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "LOOPBACK_HOSTS", "ROUTES",
           "APPROVED_EXTERNAL_BINDING_ADRS", "ExternalBindingRefused",
           "is_loopback", "check_external_binding", "ScripturaHandler",
           "describe_database", "build_router_snapshot", "serve"]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

#: Hosts that count as loopback. Anything else is an external binding.
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

#: ADRs that have approved external (non-loopback) binding. EMPTY BY DESIGN:
#: no such ADR exists. External binding therefore cannot succeed today, which is
#: the fail-closed posture required by BKB-ARCH-001 section 8.2.
APPROVED_EXTERNAL_BINDING_ADRS: frozenset[str] = frozenset()


class ExternalBindingRefused(ApiError):
    """A non-loopback binding was refused (BKB-ARCH-001 section 8.2).

    Carries the list of unmet conditions so an operator sees exactly what is
    required rather than a generic failure.
    """

    def __init__(self, host: str, unmet: tuple[str, ...]) -> None:
        self.host = host
        self.unmet_conditions = tuple(unmet)
        listing = "\n".join(f"  - {c}" for c in self.unmet_conditions)
        super().__init__(
            f"External (non-loopback) binding to {host!r} is REFUSED by default. "
            f"A read-only API is not automatically safe for public exposure. "
            f"{len(self.unmet_conditions)} condition(s) unmet:\n{listing}"
        )


def is_loopback(host: str) -> bool:
    """Return whether *host* is a loopback address."""
    return str(host).strip() in LOOPBACK_HOSTS


def check_external_binding(
    host: str,
    *,
    allow_non_loopback: bool = False,
    security_config: Any = None,
    auth_design: str | None = None,
    operator_acknowledgement: bool = False,
    external_binding_adr: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Evaluate the four-part external-binding gate (BKB-ARCH-001 section 8.2).

    An override flag does NOT independently authorize exposure: it is necessary
    but never sufficient. All four conditions must hold AND the named ADR must be
    listed in :data:`APPROVED_EXTERNAL_BINDING_ADRS`. The list is empty, so this
    always fails closed until a human-approved ADR exists.

    Returns:
        ``(permitted, unmet)`` where *unmet* names every condition not satisfied.
    """
    if is_loopback(host):
        return True, ()
    unmet: list[str] = []
    if not allow_non_loopback:
        unmet.append("explicit operator flag allow_non_loopback")
    if security_config is None:
        unmet.append("explicit security configuration")
    if not (auth_design or "").strip():
        unmet.append("documented authentication and authorization design")
    if not operator_acknowledgement:
        unmet.append("explicit operator acknowledgement")
    if not external_binding_adr or external_binding_adr not in APPROVED_EXTERNAL_BINDING_ADRS:
        unmet.append(
            "an approved external-binding ADR (none exists yet; see "
            "BKB-ARCH-001 section 8.2)"
        )
    return (not unmet), tuple(unmet)

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


def serve(
    db_path: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    allow_non_loopback: bool = False,
    security_config: Any = None,
    auth_design: str | None = None,
    operator_acknowledgement: bool = False,
    external_binding_adr: str | None = None,
) -> None:
    """Serve the read-only surface, refusing any non-loopback binding by default.

    Raises:
        ExternalBindingRefused: if *host* is not loopback and the four-part gate
            plus approved-ADR condition is not fully satisfied. The refusal
            happens BEFORE any socket is opened.
    """
    permitted, unmet = check_external_binding(
        host, allow_non_loopback=allow_non_loopback, security_config=security_config,
        auth_design=auth_design, operator_acknowledgement=operator_acknowledgement,
        external_binding_adr=external_binding_adr,
    )
    if not permitted:
        raise ExternalBindingRefused(host, unmet)

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
    parser.add_argument(
        "--allow-non-loopback", action="store_true",
        help="Necessary but NOT sufficient for external binding: the security "
             "config, auth design, operator acknowledgement, and an approved "
             "ADR are all still required (BKB-ARCH-001 section 8.2).",
    )
    args = parser.parse_args()
    if args.describe:
        print(json.dumps(build_router_snapshot(args.db), indent=2, ensure_ascii=False))
    else:
        # No warning path: a non-loopback host is REFUSED by serve() unless the
        # full four-part gate plus an approved ADR is satisfied. The flag below
        # never independently authorizes exposure.
        serve(args.db, args.host, args.port,
              allow_non_loopback=args.allow_non_loopback)

