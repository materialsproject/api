"""Primary MAPI module."""
from __future__ import annotations

import logging
import os
from importlib.metadata import PackageNotFoundError, version

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.mprester import MPRester

__all__ = ["MPRestError", "MPRester"]

try:
    __version__ = version("mp_api")
except PackageNotFoundError:  # pragma: no cover
    __version__ = os.getenv("SETUPTOOLS_SCM_PRETEND_VERSION", "")

logging.getLogger(__name__).addHandler(logging.NullHandler())
