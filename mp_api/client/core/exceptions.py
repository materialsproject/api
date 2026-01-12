"""Define custom exceptions and warnings for the client."""
from __future__ import annotations


class MPRestError(Exception):
    """Raised when the query has problems, e.g., bad query format."""


class MPRestWarning(Warning):
    """Raised when a query is malformed but interpretable."""
