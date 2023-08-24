"""Primary MAPI module."""
from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version

from .core import MPRestError
from .mprester import MPRester

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION")
