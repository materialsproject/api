"""Define custom exceptions and warnings for the client."""

from __future__ import annotations


class MPRestError(Exception):
    """Raised when the query has problems, e.g., bad query format."""


class MPRestWarning(Warning):
    """Raised when a query is malformed but interpretable."""


class MPDatasetIndexingWarning(Warning):
    """Raised during sub-optimal indexing of MPDatasets."""


class MPDatasetSlicingWarning(Warning):
    """Raised during sub-optimal slicing of MPDatasets."""


class MPDatasetIterationWarning(Warning):
    """Raised during sub-optimal iteration of MPDatasets."""
