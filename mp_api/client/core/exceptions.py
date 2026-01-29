"""Define custom exceptions and warnings for the client."""
from __future__ import annotations

import warnings

class MPRestError(Exception):
    """Raised when the query has problems, e.g., bad query format."""


class MPRestWarning(Warning):
    """Raised when a query is malformed but interpretable."""

def _emit_status_warning() -> None:
    """Emit a warning if client can't hear a heartbeat."""
    warnings.warn(
        "Cannot listen to heartbeat, check Materials Project "
        "status page: https://status.materialsproject.org/",
        category=MPRestWarning,
        stacklevel=2,
    )
