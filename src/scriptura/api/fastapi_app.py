"""Optional FastAPI surface — NOT adopted, import-guarded, inert without FastAPI.

Normative source: ADR-0004. FastAPI adoption requires an accepted ADR showing a
requirement stdlib cannot satisfy, licence compatibility of the full dependency
chain, a supply-chain assessment, and a removal path.

This module exists so the seam is defined, but it is NOT imported by default and
raises a clear, actionable error when FastAPI is absent. It exposes the SAME
read-only contract as the stdlib surface; no write endpoint may be added without
an accepted ADR.
"""

from __future__ import annotations

from typing import Any

__all__ = ["FASTAPI_ADOPTED", "build_app", "fastapi_available"]

#: Adoption flag. False until an ADR adopts FastAPI. The stdlib surface is the
#: baseline regardless of whether FastAPI happens to be installed.
FASTAPI_ADOPTED = False


def fastapi_available() -> bool:
    try:
        import fastapi  # noqa: F401
        return True
    except ImportError:
        return False


def build_app(db_path: str) -> Any:
    """Build the optional FastAPI application.

    Raises:
        RuntimeError: always at M0 — FastAPI is not adopted (ADR-0004). If it
            were adopted, this would additionally raise when the package or a
            database file is unavailable.
    """
    if not FASTAPI_ADOPTED:
        raise RuntimeError(
            "The FastAPI surface is not adopted (ADR-0004). The baseline HTTP "
            "surface is stdlib: python3 -m scriptura.api.server --db DB. "
            "Adopting FastAPI requires an accepted ADR."
        )
    if not fastapi_available():
        raise RuntimeError(
            "FastAPI is adopted but the 'fastapi' package is not installed. "
            "Install it to serve this surface."
        )
    raise RuntimeError("Unreachable: FASTAPI_ADOPTED is False at M0.")

# placeholder part 1
