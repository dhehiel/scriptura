"""Read-only HTTP surface: stdlib baseline, optional FastAPI (gated, not adopted).
"""

from __future__ import annotations

from .fastapi_app import FASTAPI_ADOPTED, build_app, fastapi_available
from .server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    ROUTES,
    ScripturaHandler,
    build_router_snapshot,
    describe_database,
    serve,
)

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ROUTES",
    "ScripturaHandler",
    "describe_database",
    "build_router_snapshot",
    "serve",
    "FASTAPI_ADOPTED",
    "build_app",
    "fastapi_available",
]
