"""Quiet mode and the single-owner logging configuration. No network access."""

import io
import logging
import subprocess
import sys
import warnings

import pytest
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client import enable_logging, is_quiet, quiet
from mp_api.client.core._display import mp_warning, print_notice, progress_bar, status
from mp_api.client.core.exceptions import MPRestWarning

CLIENT = "mp_api.client"


@pytest.fixture
def term():
    buf = io.StringIO()
    display.set_console(
        Console(file=buf, force_terminal=True, force_jupyter=False, width=120)
    )
    yield buf
    display.set_console(None)


@pytest.fixture
def app_handler():
    """An application's root handler, recording everything that reaches it."""
    records: list[logging.LogRecord] = []

    class Recorder(logging.Handler):
        def emit(self, record):
            records.append(record)

    root = logging.getLogger()
    handler = Recorder(level=logging.DEBUG)
    root.addHandler(handler)
    old_level = root.level
    root.setLevel(logging.DEBUG)
    yield records
    root.removeHandler(handler)
    root.setLevel(old_level)


def emit_everything():
    """One of each kind of client output."""
    logging.getLogger("mp_api.client.core.client").warning("core warning")
    logging.getLogger("mp_api.client.core.client").error("core error")
    from mp_api.client.contribs._logger import MPCC_LOGGER

    MPCC_LOGGER.warning("contribs warning")
    print_notice("a notice")
    with progress_bar("a bar", total=2, summary="Did {completed}") as bar:
        bar.update(2)
    with status("a status line"):
        pass
    mp_warning("an advisory")


# --------------------------------------------------------------------------
# Single owner of logging configuration
# --------------------------------------------------------------------------


def test_no_child_logger_sets_its_own_level():
    """Only `mp_api.client` is configured; children inherit its level."""
    import mp_api.client.contribs._logger  # noqa: F401 - registers its logger
    import mp_api.client.mprester  # noqa: F401

    configured = {
        name: logger.level
        for name, logger in logging.Logger.manager.loggerDict.items()
        if name.startswith(CLIENT + ".")
        and isinstance(logger, logging.Logger)
        and logger.level != logging.NOTSET
    }
    assert configured == {}


def test_one_level_controls_contribs(app_handler):
    from mp_api.client.contribs._logger import MPCC_LOGGER

    enable_logging("ERROR")
    try:
        MPCC_LOGGER.warning("hidden")
        MPCC_LOGGER.error("shown")
    finally:
        enable_logging()
    assert [r.getMessage() for r in app_handler] == ["shown"]


def test_contribs_import_does_not_change_warning_filters():
    code = (
        "import warnings, mp_api.client; before = list(warnings.filters); "
        "import mp_api.client.contribs.client; "
        "assert warnings.filters == before, 'filters changed'"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_deprecated_contribs_log_level_setting_warns():
    code = (
        "import warnings; warnings.simplefilter('error', FutureWarning)\n"
        "import mp_api.client.contribs._logger"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**_env(), "MPCONTRIBS_CLIENT_LOG_LEVEL": "DEBUG"},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "MPCONTRIBS_CLIENT_LOG_LEVEL is deprecated" in result.stderr


def test_disable_logging_is_gone():
    import mp_api.client

    assert not hasattr(mp_api.client, "disable_logging")
    assert not hasattr(display, "disable_logging")


# --------------------------------------------------------------------------
# Quiet mode
# --------------------------------------------------------------------------


def test_quiet_silences_everything(term, app_handler):
    with quiet():
        assert is_quiet()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            emit_everything()

    assert term.getvalue() == ""
    assert app_handler == []
    assert caught == []
    assert not is_quiet()


def test_outside_quiet_everything_is_emitted(term, app_handler):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        emit_everything()

    messages = [r.getMessage() for r in app_handler]
    assert {"core warning", "core error", "contribs warning"} <= set(messages)
    assert "a notice" in term.getvalue() and "✓ Did 2" in term.getvalue()
    assert [str(w.message) for w in caught] == ["an advisory"]


def test_quiet_keeps_deprecations_and_errors():
    with quiet():
        with pytest.warns(FutureWarning, match="old"):
            warnings.warn("old", FutureWarning, stacklevel=1)
        with pytest.raises(ValueError):
            raise ValueError("still raised")


def test_quiet_restores_previous_state_and_nests():
    enable_logging("WARNING")
    try:
        with quiet():
            assert logging.getLogger(CLIENT).level > logging.CRITICAL
            with quiet():
                pass
            assert is_quiet()  # inner exit restores the outer (quiet) state
            with quiet(False):
                assert not is_quiet()
                assert logging.getLogger(CLIENT).level == logging.WARNING
            assert is_quiet()
        assert not is_quiet()
        assert logging.getLogger(CLIENT).level == logging.WARNING
    finally:
        enable_logging()


def test_quiet_as_plain_call():
    quiet()
    try:
        assert is_quiet()
    finally:
        quiet(False)
    assert not is_quiet()


def test_enable_logging_while_quiet_applies_after():
    with quiet():
        enable_logging("ERROR")
        assert logging.getLogger(CLIENT).level > logging.CRITICAL
    try:
        assert logging.getLogger(CLIENT).level == logging.ERROR
    finally:
        enable_logging()


def test_quiet_does_not_touch_warning_filters():
    before = list(warnings.filters)
    with quiet():
        assert warnings.filters == before
    assert warnings.filters == before


def test_mprester_quiet_kwarg(monkeypatch, term):
    from mp_api.client import MPRester
    from mp_api.client.core.client import _Rester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))

    MPRester(api_key="a" * 32, quiet=False)
    assert not is_quiet()
    MPRester(api_key="a" * 32, quiet=True)
    assert is_quiet()
    MPRester(api_key="a" * 32, quiet=False)  # doesn't undo it
    assert is_quiet()


def test_quiet_setting_at_import():
    code = (
        "import logging, mp_api.client as c\n"
        "assert c.is_quiet()\n"
        "logging.getLogger('mp_api.client.core').warning('nope')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**_env(), "MPRESTER_QUIET": "true"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == "" and result.stdout == ""


def test_status_silent_when_disabled(term, app_handler):
    with status("muted", enabled=False):
        pass
    assert term.getvalue() == "" and app_handler == []


def _env() -> dict[str, str]:
    import os

    return {k: v for k, v in os.environ.items() if not k.startswith("MPRESTER_")}


# --------------------------------------------------------------------------
# DatabaseVersions display
# --------------------------------------------------------------------------


def test_database_versions_is_a_plain_dict():
    import json

    from mp_api.client.core._display import DatabaseVersions

    data = {"summary": ["2026.04.13", "2026.09.28"], "thermo": ["2026.04.13"]}
    v = DatabaseVersions(data, current="2026.04.13")
    assert v == data and isinstance(v, dict)
    assert json.loads(json.dumps(v)) == data
    assert v["thermo"] == ["2026.04.13"] and list(v) == ["summary", "thermo"]


def test_database_versions_repr_is_a_table():
    from mp_api.client.core._display import DatabaseVersions

    v = DatabaseVersions(
        {"summary": ["2026.04.13", "2026.09.28"], "thermo": ["2026.09.28"]},
        current="2026.04.13",
    )
    text = repr(v)  # not an interactive colour terminal: plain text
    assert "Database versions available on S3" in text
    assert "│ summary │ 2026.04.13*, 2026.09.28 │" in text
    assert "│ thermo  │ 2026.09.28              │" in text
    assert "2026.04.13* served by the API" in text
    assert "newer" not in text  # colour legend only shown with colours
    assert "\x1b[" not in text
    assert str(v) == text
    assert repr(DatabaseVersions({})) == "DatabaseVersions({})"


def test_database_versions_no_marker_without_current():
    from mp_api.client.core._display import DatabaseVersions

    text = repr(DatabaseVersions({"summary": ["2026.09.28"]}, current="2026.04.13"))
    assert "*" not in text and "served by the API" not in text


def test_database_versions_colours(monkeypatch):
    from mp_api.client.core._display import MP_THEME, DatabaseVersions

    v = DatabaseVersions(
        {"chemenv": ["2025.09.25", "2026.04.13", "2026.09.28"]}, current="2026.04.13"
    )
    assert [v._style(x) for x in v["chemenv"]] == [
        "mp.version.older",
        "mp.version.current",
        "mp.version.newer",
    ]
    assert DatabaseVersions(v, current=None)._style("2026.04.13") == ""

    def rgb(style):
        c = MP_THEME.styles[style].color.triplet
        return f"38;2;{c.red};{c.green};{c.blue}"

    monkeypatch.setattr(display, "_interactive_color", lambda: True)
    monkeypatch.setattr(display, "_color_system", lambda: "truecolor")
    coloured = repr(v)
    for style in ("mp.version.current", "mp.version.newer", "mp.version.older"):
        assert rgb(style) in coloured
    assert "newer" in coloured and "older" in coloured  # legend
    assert "\x1b[" not in str(v)  # str() is always plain


def test_database_versions_colour_only_when_interactive(monkeypatch):
    import sys

    from mp_api.client.core._display import _interactive_color

    monkeypatch.delattr(sys, "ps1", raising=False)
    assert not _interactive_color()  # a script, or pytest
    monkeypatch.setattr(sys, "ps1", ">>> ", raising=False)

    class TTY(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdout", TTY())
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    assert _interactive_color()
    monkeypatch.setenv("NO_COLOR", "1")
    assert not _interactive_color()


def test_database_versions_notebook_and_ipython():
    pytest.importorskip("IPython")
    from IPython.core.formatters import DisplayFormatter

    from mp_api.client.core._display import DatabaseVersions

    v = DatabaseVersions({"summary": ["2026.04.13"]}, current="2026.04.13")
    data, _ = DisplayFormatter().format(v)
    assert data["text/plain"] == repr(v)  # IPython terminal: the table, not a dict
    assert data["text/html"].startswith("<pre>")
    assert "summary" in data["text/html"]
    assert "color: #48c78e" in data["text/html"]  # current version, green
