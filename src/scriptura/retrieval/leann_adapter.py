"""Optional LEANN semantic retrieval adapter.

LEANN is an OPTIONAL backend: never mandatory, never load-bearing, never assumed
present. Absence is a degraded mode, not an error (ADR-0006).

Verified facts about LEANN (PyPI, M0 research; NOT verified by execution here —
package-index access is unavailable in this environment): package ``leann``,
release 0.3.9, MIT, Python >= 3.10, hnsw/diskann/ivf backends,
LeannBuilder/LeannSearcher/LeannChat. The storage-efficiency claim is the
vendor's, not Scriptura's.

Importing this module must NEVER fail for lack of LEANN.
"""

from __future__ import annotations

import importlib.util
import pathlib
from typing import Any, Iterable

from ..core.errors import CapabilityError, RetrievalError
from .interface import BACKEND_SEMANTIC, BackendStatus, RetrievalResult

__all__ = [
    "LEANN_PACKAGE",
    "LeannAdapter",
    "LeannUnavailableError",
    "leann_available",
    "leann_version",
]

LEANN_PACKAGE = "leann"
_REQUIRED_ENTRYPOINTS = ("LeannBuilder", "LeannSearcher")


class LeannUnavailableError(CapabilityError):
    """LEANN is not installed or not usable. Degrade to FTS5."""


def leann_available() -> bool:
    return importlib.util.find_spec(LEANN_PACKAGE) is not None


def leann_version() -> str | None:
    if not leann_available():
        return None
    try:
        from importlib.metadata import version
        return version(LEANN_PACKAGE)
    except Exception:
        return None


def _require_entrypoints() -> tuple[Any, Any]:
    try:
        module = __import__(LEANN_PACKAGE, fromlist=list(_REQUIRED_ENTRYPOINTS))
    except ImportError as exc:
        raise LeannUnavailableError(
            f"The optional '{LEANN_PACKAGE}' package is not installed. Install it "
            f"to enable semantic retrieval, or use the FTS5 baseline. ({exc})"
        ) from exc
    missing = [n for n in _REQUIRED_ENTRYPOINTS if not hasattr(module, n)]
    if missing:
        raise LeannUnavailableError(
            f"Installed '{LEANN_PACKAGE}' lacks {', '.join(missing)}. Degrading to FTS5."
        )
    return getattr(module, "LeannBuilder"), getattr(module, "LeannSearcher")



class LeannAdapter:
    """Semantic backend over an installed LEANN package.

    Opens an EXISTING operator-built index; Scriptura never builds one
    unprompted. Embedding generation is out of scope for M0 (ADR-0006 rule 8).
    """

    backend_id = BACKEND_SEMANTIC

    def __init__(self, index_path: str | pathlib.Path) -> None:
        builder_cls, searcher_cls = _require_entrypoints()
        self._builder_cls = builder_cls
        self._searcher_cls = searcher_cls
        self.index_path = pathlib.Path(index_path)
        self._searcher: Any = None

    def is_available(self) -> bool:
        return leann_available() and self.index_path.exists()

    def status(self) -> BackendStatus:
        if not leann_available():
            return BackendStatus(
                backend=self.backend_id, available=False,
                reason=f"'{LEANN_PACKAGE}' is not installed. Degraded mode: FTS5.",
            )
        return BackendStatus(
            backend=self.backend_id, available=self.index_path.exists(),
            reason=(
                f"installed version {leann_version() or 'unknown'}; index "
                f"{'present' if self.index_path.exists() else 'ABSENT at ' + str(self.index_path)}"
            ),
        )

    def _open(self) -> Any:
        if self._searcher is None:
            if not self.index_path.exists():
                raise LeannUnavailableError(
                    f"No LEANN index at {self.index_path}. The operator builds one; "
                    f"Scriptura does not build indexes unprompted."
                )
            try:
                self._searcher = self._searcher_cls(str(self.index_path))
            except Exception as exc:
                raise RetrievalError(
                    f"Could not open LEANN index at {self.index_path}: {exc}"
                ) from exc
        return self._searcher

    def search(
        self, query: str, *, limit: int = 50, layers: Iterable[Any] | None = None,
    ) -> tuple[RetrievalResult, ...]:
        if not query or not query.strip():
            raise RetrievalError("Semantic query must be a non-empty string.")
        if limit < 1:
            raise RetrievalError(f"limit must be at least 1, got {limit}.")
        allowed = (
            None if layers is None
            else {str(getattr(la, "value", la)) for la in layers}
        )
        try:
            raw = self._open().search(query, top_k=limit)
        except LeannUnavailableError:
            raise
        except Exception as exc:
            raise RetrievalError(f"LEANN search failed: {exc}") from exc
        out: list[RetrievalResult] = []
        for hit in raw or ():
            if isinstance(hit, dict):
                record_id = str(hit.get("id", hit.get("record_id", "")))
                layer = str(hit.get("layer", "ai_hypothesis"))
                text = str(hit.get("text", ""))
                try:
                    score = float(hit.get("score", 0.0))
                except (TypeError, ValueError):
                    score = 0.0
            else:  # pragma: no cover - shape depends on installed LEANN
                record_id, layer, text, score = str(hit), "ai_hypothesis", "", 0.0
            if allowed is not None and layer not in allowed:
                continue
            out.append(
                RetrievalResult(
                    record_id=record_id, layer=layer,
                    non_authoritative=(layer == "ai_hypothesis"), text=text,
                    score=score, backend=self.backend_id,
                    extra={"index_path": str(self.index_path)},
                )
            )
        return tuple(out)

