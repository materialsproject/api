"""Importing / using contribs must not change process-wide state."""

import importlib
import logging
import subprocess
import sys
import warnings

import pytest
from swagger_spec_validator.common import SwaggerValidationError

from mp_api.client.core.exceptions import MPContribsClientError


def test_import_has_no_global_side_effects():
    """Checked in a fresh interpreter, so earlier imports can't mask anything."""
    code = """
import logging, warnings
import pandas as pd
import plotly.io as pio

fmt = warnings.formatwarning
backend = pd.options.plotting.backend
template = pio.templates.default

import mp_api.client.contribs.client  # noqa

assert warnings.formatwarning is fmt, "warnings.formatwarning changed"
assert pd.options.plotting.backend == backend, "pandas plotting backend changed"
assert pio.templates.default == template, "plotly template changed"
assert logging.getLogger("mp_api.client.contribs").handlers == [], "handlers added"
print("ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


@pytest.mark.parametrize(
    "func, arg",
    [
        ("validate_email", "not-an-email"),
        ("validate_email", "nope:someone@example.com"),
        ("validate_url", "example"),
    ],
)
def test_validation_errors_are_backwards_compatible(func, arg):
    client = importlib.import_module("mp_api.client.contribs.client")
    from mp_api.client.contribs.utils import MPContribsValidationError

    with pytest.raises(MPContribsValidationError) as excinfo:
        getattr(client, func)(arg)
    assert isinstance(excinfo.value, SwaggerValidationError)
    assert isinstance(excinfo.value, MPContribsClientError)


def test_short_traceback_hook():
    err = MPContribsClientError("Invalid API key: abc")
    assert err._render_traceback_() == ["MPContribsClientError: Invalid API key: abc"]


def test_ipython_showtraceback_not_patched():
    pytest.importorskip("IPython")
    from IPython.core.interactiveshell import InteractiveShell

    original = InteractiveShell.showtraceback
    importlib.reload(importlib.import_module("mp_api.client.contribs.utils"))
    assert InteractiveShell.showtraceback is original


def test_contribs_logger_has_no_handlers_and_propagates():
    from mp_api.client.contribs._logger import MPCC_LOGGER

    assert MPCC_LOGGER.logger.handlers == []
    assert MPCC_LOGGER.logger.propagate


def test_mute_progress_bars_forwarded(monkeypatch):
    from mp_api.client import MPRester
    from mp_api.client.contribs import client as contribs_client

    captured = {}

    class FakeContribs:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(contribs_client, "ContribsClient", FakeContribs)
    monkeypatch.setattr(
        MPRester, "_get_heartbeat_info", staticmethod(lambda endpoint: ("v", []))
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mpr = MPRester(api_key="a" * 32, mute_progress_bars=True)
    assert isinstance(mpr.contribs, FakeContribs)
    assert captured["mute_progress_bars"] is True


def test_run_futures_progress_respects_disable(monkeypatch):
    from mp_api.client.contribs import client as contribs_client

    seen = {}
    real = contribs_client.progress_bar

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(contribs_client, "progress_bar", spy)
    contribs_client._run_futures([], disable=True)
    assert seen["enabled"] is False and seen["delay"] == 5
    contribs_client._run_futures([], disable=False, desc="Submit")
    assert seen["enabled"] is True


def test_logging_does_not_go_to_stdout(capsys):
    from mp_api.client.contribs._logger import MPCC_LOGGER

    logging.getLogger().handlers  # pytest attaches capture handlers to root
    MPCC_LOGGER.info("Nothing to submit.")
    out, _ = capsys.readouterr()
    assert out == ""
