"""Logger for the MPContribs client.

Records go through the `mp_api.client` logger's default handler (stderr),
see `mp_api.client.core._display`. No handlers or level are set here: the
level is configured once, for the whole client, with `MPRESTER_LOG_LEVEL`.
"""

from __future__ import annotations

import logging
import os
import warnings

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
    return CustomLoggerAdapter(logger, cfg)


if MPCC_SETTINGS.CLIENT_LOG_LEVEL is not None:
    warnings.warn(
        "MPCONTRIBS_CLIENT_LOG_LEVEL is deprecated and ignored, use MPRESTER_LOG_LEVEL "
        "(which sets the level for the whole client) instead.",
        FutureWarning,
        stacklevel=2,
    )


MPCC_LOGGER = get_logger()
