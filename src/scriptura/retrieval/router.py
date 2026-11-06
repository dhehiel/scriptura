"""Capability-based retrieval routing.

The router probes capabilities at CONSTRUCTION and selects a backend. It NEVER
assumes the optional backend is present. Absence of LEANN is a degraded mode,
reported as such — not an error. The router reports which backend served every
request; results from different backends are never silently mixed.

A caller may PIN a backend. Pinning an unavailable backend RAISES rather than
silently falling back: silent fallback would misrepresent what served the query.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable

from ..core.errors import CapabilityError, RetrievalError
from .interface import (
    BACKEND_FTS5,
    BACKEND_SEMANTIC,
    BackendStatus,
    RetrievalBackend,
    RetrievalResult,
)
from .leann_adapter import LeannAdapter, leann_available

__all__ = ["RouteDecision", "RetrievalRouter"]


@dataclass(frozen=True)
class RouteDecision:
    """Which backend served a request, and why."""

    backend: str
    requested: str | None
    degraded: bool
    reason: str


class _FtsBackend:
    """The always-available FTS5 baseline, behind the backend interface."""

    backend_id = BACKEND_FTS5

    def __init__(self, conn: sqlite3.Connection) -> None:
        from ..search import FtsIndex
        self._fts = FtsIndex(conn)

    def is_available(self) -> bool:
        return self._fts.is_available()

    def status(self) -> BackendStatus:
        ok = self.is_available()
        return BackendStatus(
            backend=self.backend_id, available=ok,
            reason="FTS5 baseline present." if ok else "FTS5 indexes missing.",
        )

    def search(
        self, query: str, *, limit: int = 50, layers: Iterable[Any] | None = None,
    ) -> tuple[RetrievalResult, ...]:
        hits = self._fts.search_corpus(query, limit=limit, layers=layers)
        return tuple(
            RetrievalResult(
                record_id=h.record_id, layer=h.layer,
                non_authoritative=h.non_authoritative, text=h.text,
                score=h.rank, backend=self.backend_id,
                extra={"edition_id": h.edition_id, "reference": h.reference_display},
                edition_source=h.edition_id or h.source_uri,
                verification_status=h.verification_status,
            )
            for h in hits
        )


class RetrievalRouter:
    """Route retrieval requests across backends by capability."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        leann_index_path: str | None = None,
        default_backend: str = BACKEND_FTS5,
    ) -> None:
        self._fts = _FtsBackend(conn)
        self._leann: LeannAdapter | None = None
        if leann_index_path is not None:
            try:
                candidate = LeannAdapter(leann_index_path)
                if leann_available():
                    self._leann = candidate
            except CapabilityError:
                self._leann = None
        if default_backend not in (BACKEND_FTS5, BACKEND_SEMANTIC):
            raise RetrievalError(f"Unknown backend {default_backend!r}.")
        self._default = default_backend

    @property
    def default_backend(self) -> str:
        return self._default

    def statuses(self) -> tuple[BackendStatus, ...]:
        out = [self._fts.status()]
        out.append(
            self._leann.status()
            if self._leann is not None
            else BackendStatus(
                backend=BACKEND_SEMANTIC, available=False,
                reason="LEANN backend not configured. Degraded mode: FTS5.",
            )
        )
        return tuple(out)

    def search(
        self, query: str, *, limit: int = 50,
        layers: Iterable[Any] | None = None, backend: str | None = None,
    ) -> tuple[tuple[RetrievalResult, ...], RouteDecision]:
        """Search via the pinned or default backend.

        Returns (hits, decision). Pinning an unavailable backend RAISES.
        """
        pinned = backend if backend is not None else self._default
        if pinned == BACKEND_SEMANTIC:
            if self._leann is None or not self._leann.is_available():
                raise CapabilityError(
                    "Semantic backend pinned but unavailable "
                    f"({self._semantic_reason()}). Pinning an unavailable backend "
                    "raises rather than silently falling back."
                )
            return self._leann.search(query, limit=limit, layers=layers), RouteDecision(
                backend=BACKEND_SEMANTIC, requested=backend, degraded=False,
                reason="Pinned semantic backend served the request.",
            )
        if pinned != BACKEND_FTS5:
            raise RetrievalError(f"Unknown backend {pinned!r}.")
        degraded = self._leann is not None and backend is None and self._default == BACKEND_FTS5
        return self._fts.search(query, limit=limit, layers=layers), RouteDecision(
            backend=BACKEND_FTS5, requested=backend, degraded=False,
            reason=(
                "FTS5 baseline served the request."
                + (" Semantic backend unavailable; degraded mode." if self._leann is None else "")
            ),
        )

    def _semantic_reason(self) -> str:
        if not leann_available():
            return "'leann' package not installed"
        if self._leann is None:
            return "no LEANN index configured"
        return self._leann.status().reason

