from __future__ import annotations

import logging
import os
import sys
from io import StringIO

from mp_api.client.contribs.settings import MPCC_SETTINGS


class LogFilter(logging.Filter):
    def __init__(self, level: int, *args, **kwargs) -> None:
        """Start an instance of logging.Filter.

        Args:
            level (int) : logging level
            *args : args to pass to logging.Filter
            **kwargs : kwargs to pass to logging.Filter
        """
        self.level = level
        super().__init__(*args, **kwargs)

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter whether a message is logged.

        Args:
            record (logging.LogRecord) : message to test if it
                meets threshold for logging.

        Returns:
            bool : True if message should be suppressed.
        """
        return record.levelno < self.level


class CustomLoggerAdapter(logging.LoggerAdapter):
    """Adapter for logger to enable prefixing."""

    def process(self, msg, kwargs):
        """Prefix logging message.

        Args:
            msg (str) : logging message
            kwargs : args to pass to logging.LoggerAdapter
        """
        prefix = self.extra.get("prefix")
        return f"[{prefix}] {msg}" if prefix else msg, kwargs


def get_logger(name: str = "mp_api.client.contribs") -> CustomLoggerAdapter:
    """Get the default MPContribs logger.

    Args:
        name (str) : name of the logger
    Returns:
        CustomLoggerAdapter
    """
    logger = logging.getLogger(name)
    process = os.environ.get("SUPERVISOR_PROCESS_NAME")
    group = os.environ.get("SUPERVISOR_GROUP_NAME")
    cfg = {"prefix": f"{group}/{process}"} if process and group else {}
    info_handler = logging.StreamHandler(sys.stdout)
    error_handler = logging.StreamHandler(sys.stderr)
    info_handler.addFilter(LogFilter(logging.WARNING))
    error_handler.setLevel(max(logging.DEBUG, logging.WARNING))
    logger.handlers = [info_handler, error_handler]
    logger.setLevel(MPCC_SETTINGS.CLIENT_LOG_LEVEL)
    return CustomLoggerAdapter(logger, cfg)


MPCC_LOGGER = get_logger()


class TqdmToLogger(StringIO):
    logger: logging.LoggerAdapter = MPCC_LOGGER
    level: int | str = MPCC_SETTINGS.CLIENT_LOG_LEVEL
    buf: str = ""

    def __init__(
        self, logger: logging.LoggerAdapter = MPCC_LOGGER, level: int | None = None
    ) -> None:
        """Start an instance of a TQDM logger.

        Args:
            logger (logging.Logger) : Logger to pass through
            level (int) : logging level
        """
        super().__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf: str) -> int:
        self.buf = buf.strip("\r\n\t ")
        return 1

    def flush(self) -> None:
        self.logger.log(self.level, self.buf)
