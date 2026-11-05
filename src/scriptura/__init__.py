"""Scriptura: Biblical Knowledge and Research Infrastructure.

Public package surface. Importing this package requires only the standard
library (ADR-0002). Optional integrations (``leann``, ``fastapi``) are
import-guarded in their own modules and are never imported here.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
