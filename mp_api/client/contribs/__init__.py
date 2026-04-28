"""Pull in core MPContribs client features."""

from __future__ import annotations

from mp_api.client.contribs._types import Attachment, Table
from mp_api.client.contribs.client import ContribsClient
from mp_api.client.contribs.settings import MPCC_SETTINGS
from mp_api.client.core.exceptions import MPContribsClientError

__all__ = [
    "ContribsClient",
    "MPContribsClientError",
    "MPCC_SETTINGS",
    "Table",
    "Attachment",
]
