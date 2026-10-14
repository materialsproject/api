"""Primary MAPI module."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version

from mp_api.client.core._display import (
    _configure_from_settings,
    enable_logging,
    is_quiet,
    quiet,
)
from mp_api.client.core.exceptions import MPRestError
from mp_api.client.mprester import MPRester

__all__ = ["MPRestError", "MPRester", "enable_logging", "is_quiet", "quiet"]

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION", "")

_configure_from_settings()
