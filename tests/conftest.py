"""Test-wide fixtures."""

import logging

import pytest

import mp_api.client.core._display as display


@pytest.fixture(autouse=True)
def _restore_client_output():
    """Undo process-wide output settings a test changed (quiet mode, log level).

    Quiet mode is deliberately process-wide, so e.g. creating an MCP client
    (which requests quiet) would otherwise silence every later test.
    """
    logger = logging.getLogger(display.LOGGER_NAME)
    was_quiet = display.is_quiet()
    level = logger.level if not was_quiet else display._QUIET.saved_level
    yield
    display.quiet(was_quiet)
    if not was_quiet:
        logger.setLevel(level)
