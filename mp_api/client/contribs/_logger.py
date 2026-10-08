"""Logger for the MPContribs client.

Records go through the `mp_api.client` logger's default handler (stderr),
see `mp_api.client.core._display`. No handlers are attached here.
"""

from __future__ import annotations

import logging
import os

from mp_api.client.contribs.settings import MPCC_SETTINGS


class CustomLoggerAdapter(logging.LoggerAdapter):
    """Prefix messages with the supervisor group/process, if running under supervisor."""

    def process(self, msg, kwargs):
        prefix = self.extra.get("prefix")  # type: ignore[union-attr]
        return f"[{prefix}] {msg}" if prefix else msg, kwargs


def get_logger(name: str = "mp_api.client.contribs") -> CustomLoggerAdapter:
    """Get the contribs logger.

    Args:
        name (str) : logger name, a child of `mp_api.client`

    Returns:
        CustomLoggerAdapter
    """
    logger = logging.getLogger(name)
    process = os.environ.get("SUPERVISOR_PROCESS_NAME")
    group = os.environ.get("SUPERVISOR_GROUP_NAME")
    cfg = {"prefix": f"{group}/{process}"} if process and group else {}
    logger.setLevel(MPCC_SETTINGS.CLIENT_LOG_LEVEL)
    return CustomLoggerAdapter(logger, cfg)


MPCC_LOGGER = get_logger()
