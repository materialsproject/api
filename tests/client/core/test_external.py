"""Routing other libraries' warnings / log records through the client. No network."""

from __future__ import annotations

import inspect
import io
import logging
import os
import re
import sys
import threading
import types
import warnings
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client import quiet
from mp_api.client.core._display import MP_THEME, mp_deprecation, mp_warning
from mp_api.client.core._external import (
    EXTERNAL_LOGGER,
    _WarningHook,
    capturing,
    in_current_context,
    is_capturing,
    track_calls,
)
from mp_api.client.core.exceptions import MPRestWarning

LIB_SOURCE = """
import logging, warnings

log = logging.getLogger("fakelib.core")

def process(i):
    warnings.warn(f"WARNING! Discarding entry mp-{i}", stacklevel=2)

def deprecated():
    warnings.warn("old api", DeprecationWarning, stacklevel=2)

def runtime():
    warnings.warn("divide by zero", RuntimeWarning)

def logs():
    log.warning("library log record")
"""


@pytest.fixture
def fakelib(tmp_path, monkeypatch):
    """A third-party package that warns with `stacklevel=2`, as pymatgen does."""
    pkg = tmp_path / "fakelib"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(LIB_SOURCE)
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "fakelib", raising=False)
    import fakelib

    return fakelib


@pytest.fixture(autouse=True)
def routed():
    """Chain the client's warnings hook over pytest's.

    pytest runs each test inside `catch_warnings(record=True)`, which replaces
    `warnings.showwarning`, exactly the "application replaced the hook" case
    the client respects. Chaining it back in mirrors a session where nothing
    replaced it, while pytest's recorder still sees what passes through.
    """
    previous = warnings.showwarning
    warnings.showwarning = _WarningHook(previous)
    yield
    warnings.showwarning = previous


@pytest.fixture
def records():
    """Records reaching `mp_api.client.external`, whatever handlers are set up."""
    seen: list[logging.LogRecord] = []

    class Recorder(logging.Handler):
        def emit(self, record):
            seen.append(record)

    logger = logging.getLogger(EXTERNAL_LOGGER)
    handler = Recorder(level=logging.DEBUG)
    logger.addHandler(handler)
    yield seen
    logger.removeHandler(handler)


@pytest.fixture
def no_app_logging(monkeypatch):
    """An application that hasn't configured logging: the client's records go
    to its default handler, not to pytest's root handlers."""
    monkeypatch.setattr(display, "_app_handlers", lambda logger: [])


@contextmanager
def unhandled(logger: logging.Logger):
    """Make `logger`'s records reach no handler, so Python uses `lastResort`.

    pytest attaches capture handlers to the root logger, and to loggers that
    don't propagate, for each test phase, so this is applied in the test body.
    """
    propagate, handlers = logger.propagate, logger.handlers
    logger.propagate, logger.handlers = False, []
    try:
        yield
    finally:
        logger.propagate, logger.handlers = propagate, handlers


def _console(terminal: bool) -> tuple[Console, io.StringIO]:
    buf = io.StringIO()
    console = Console(
        file=buf,
        force_terminal=terminal,
        force_jupyter=False,
        theme=MP_THEME,
        width=200,
        color_system="truecolor" if terminal else None,
    )
    return console, buf


@pytest.fixture
def term(no_app_logging):
    console, buf = _console(terminal=True)
    display.set_console(console)
    yield buf
    display.set_console(None)


@pytest.fixture
def pipe(no_app_logging):
    console, buf = _console(terminal=False)
    display.set_console(console)
    yield buf
    display.set_console(None)


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


@track_calls
class Client:
    """Stands in for a rester."""

    def __init__(self, lib=None):
        self.lib = lib

    def run(self, n: int = 1, *, flag: bool = False) -> str:
        """Docs."""
        for i in range(n):
            self.lib.process(i)
        return "done"

    def nested(self):
        assert is_capturing()
        return self.run()

    @staticmethod
    def static_call(lib):
        lib.process(7)

    def advise(self):
        mp_warning("check your arguments", stacklevel=2)

    def deprecated_api(self):
        mp_deprecation("use something else", stacklevel=2)

    def _private(self):
        return is_capturing()

    @property
    def prop(self):
        return is_capturing()


# --- capturing / wrapping -------------------------------------------------------


def test_public_methods_capture_private_and_properties_dont():
    client = Client()
    assert not is_capturing()
    assert client._private() is False and client.prop is False
    assert Client.nested.__mp_tracked__


def test_wrapping_preserves_signature_and_is_idempotent():
    signature = inspect.signature(Client.run)
    assert list(signature.parameters) == ["self", "n", "flag"]
    assert Client.run.__doc__ == "Docs."
    run = Client.run
    track_calls(Client)
    assert Client.run is run  # not wrapped twice


def test_resters_are_tracked():
    from mp_api.client import MPRester
    from mp_api.client.core.client import BaseRester
    from mp_api.client.core.utils import MPDataset
    from mp_api.client.routes.materials.thermo import ThermoRester

    assert MPRester.get_stability.__mp_tracked__
    assert MPRester.__init__.__mp_tracked__
    assert BaseRester.count.__mp_tracked__
    assert ThermoRester.get_phase_diagram_from_chemsys.__mp_tracked__
    assert MPDataset.__getitem__.__mp_tracked__


# --- warnings ------------------------------------------------------------------


def test_library_warning_becomes_attributed_record(fakelib, records):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        assert Client(fakelib).run(2) == "done"
    assert [r.levelno for r in records] == [logging.WARNING] * 2
    record = records[0]
    assert record.name == f"{EXTERNAL_LOGGER}.fakelib"
    # the library line that warned, not the caller `stacklevel=2` points at
    assert record.pathname == fakelib.__file__ and record.lineno == 7
    assert record.mp_origin == "fakelib/__init__.py:7"
    assert record.mp_message == "WARNING! Discarding entry mp-0"
    assert record.getMessage() == (
        "WARNING! Discarding entry mp-0 (fakelib/__init__.py:7)"
    )


def test_every_category_is_logged_at_warning_with_its_name(fakelib, records):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        with capturing():
            fakelib.runtime()
    assert records[0].levelno == logging.WARNING
    assert records[0].mp_message == "RuntimeWarning: divide by zero"


def test_outside_client_calls_warnings_are_untouched(fakelib, records):
    with pytest.warns(UserWarning, match="Discarding entry mp-0"):
        fakelib.process(0)
    assert not records


def test_library_deprecations_pass_through(fakelib, records):
    with pytest.warns(DeprecationWarning, match="old api"), capturing():
        fakelib.deprecated()
    assert not records


def test_client_warnings_pass_through(records):
    client = Client()
    with pytest.warns(MPRestWarning, match="check your arguments"):
        client.advise()
    with pytest.warns(FutureWarning, match="use something else"):
        client.deprecated_api()
    assert not records


def test_client_warnings_point_past_the_wrappers(recwarn):
    warnings.simplefilter("always")
    Client().advise()
    Client().deprecated_api()
    assert [w.filename for w in recwarn] == [__file__] * 2


@pytest.mark.parametrize("action", ["error", "ignore", "once"])
def test_warning_filters_apply_first(fakelib, records, action):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.filterwarnings(action, message="WARNING! Discarding")
        if action == "error":
            with pytest.raises(UserWarning):
                Client(fakelib).run()
        else:
            Client(fakelib).run(1)
            Client(fakelib).run(1)
    assert len(records) == {"error": 0, "ignore": 0, "once": 1}[action]


def test_replaced_showwarning_gets_everything(fakelib, records):
    """E.g. `pytest.warns`: the application's hook wins, without being displaced."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Client(fakelib).run()
    assert [str(w.message) for w in caught] == ["WARNING! Discarding entry mp-0"]
    assert not records


def test_quiet_silences_library_warnings(fakelib, records, capsys):
    with quiet(), warnings.catch_warnings():
        warnings.simplefilter("always")
        Client(fakelib).run(3)
    assert not records
    assert capsys.readouterr().err == ""


# --- threads -------------------------------------------------------------------


def test_nested_calls_and_static_methods(fakelib, records):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        Client(fakelib).nested()
        Client.static_call(fakelib)
    assert len(records) == 2
    assert not is_capturing()


def test_client_pools_carry_the_call_context(fakelib, records):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        with capturing(), ThreadPoolExecutor(2) as pool:
            assert all(pool.map(in_current_context(lambda _: is_capturing()), [1, 2]))
            list(pool.map(in_current_context(fakelib.process), [1, 2]))
    assert len(records) == 2


def test_unrelated_threads_are_not_captured(fakelib, records):
    seen = []
    with capturing():
        thread = threading.Thread(target=lambda: seen.append(is_capturing()))
        thread.start()
        thread.join()
    assert seen == [False]


def test_multi_thread_requests_run_in_call_context(monkeypatch):
    from mp_api.client.core.client import BaseRester

    rester = BaseRester.__new__(BaseRester)
    seen = []

    def func(**params):
        seen.append(is_capturing())
        return [params], 1

    with capturing():
        rester._multi_thread(func, [{"a": 1}, {"a": 2}])
    assert seen == [True, True]


# --- library logging -----------------------------------------------------------


def test_fallback_log_records_are_routed(fakelib, records, capsys):
    with unhandled(fakelib.log):
        with capturing():
            fakelib.logs()
        assert [r.mp_message for r in records] == ["library log record"]
        assert records[0].name == f"{EXTERNAL_LOGGER}.fakelib"
        assert records[0].levelno == logging.WARNING
        assert records[0].mp_origin == "fakelib/__init__.py:16"

        records.clear()
        fakelib.logs()  # outside client calls: Python's usual fallback to stderr
    assert not records
    assert capsys.readouterr().err == "library log record\n"


def test_fallback_log_records_silenced_by_quiet(fakelib, records, capsys):
    with unhandled(fakelib.log), quiet(), capturing():
        fakelib.logs()
    assert not records and capsys.readouterr().err == ""


def test_configured_app_logging_is_untouched(fakelib, records):
    """With handlers on the root logger (pytest's here), the fallback isn't used."""
    with capturing():
        fakelib.logs()
    assert not records


# --- rendering -----------------------------------------------------------------


def test_terminal_rendering(fakelib, term):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        Client(fakelib).run()
    raw = term.getvalue()
    lines = [line.rstrip() for line in plain(raw).splitlines()]
    assert lines[0].split() == [
        "WARNING",
        "mp_api.client.external.fakelib",
        "WARNING!",
        "Discarding",
        "entry",
        "mp-0",
    ]
    assert lines[1].strip() == "fakelib/__init__.py:7"
    assert lines[1].index("fakelib") == lines[0].index("mp_api")  # message column
    # level amber, logger name secondary, origin muted, message unstyled
    assert "\x1b[38;2;214;158;0mWARNING" in raw
    assert "\x1b[38;2;147;159;200mmp_api.client.external.fakelib" in raw
    assert "\x1b[38;2;122;122;122mfakelib/__init__.py:7" in raw
    assert "WARNING! Discarding entry mp-0" in raw  # no highlighting codes inside


def test_client_messages_are_not_highlighted(term):
    logging.getLogger("mp_api.client.core").warning("Reused 12 entries for mp-149")
    assert "Reused 12 entries for mp-149" in term.getvalue()


def test_plain_rendering_is_one_line(fakelib, pipe):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        Client(fakelib).run()
    assert pipe.getvalue() == (
        "mp_api.client.external.fakelib - WARNING - "
        "WARNING! Discarding entry mp-0 (fakelib/__init__.py:7)\n"
    )


def test_per_library_level(fakelib, pipe):
    logger = logging.getLogger(f"{EXTERNAL_LOGGER}.fakelib")
    logger.setLevel(logging.ERROR)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            Client(fakelib).run()
    finally:
        logger.setLevel(logging.NOTSET)
    assert pipe.getvalue() == ""


# --- deprecations --------------------------------------------------------------


def test_quiet_keeps_deprecations_by_default():
    with quiet(), pytest.warns(FutureWarning):
        Client().deprecated_api()


def test_quiet_deprecations(recwarn):
    warnings.simplefilter("always")
    with quiet(deprecations=True):
        Client().deprecated_api()
        mp_deprecation("direct")
    assert not recwarn
    with pytest.warns(FutureWarning):  # restored on exit
        Client().deprecated_api()


def test_deprecations_flag_needs_quiet(recwarn):
    warnings.simplefilter("always")
    with quiet(False, deprecations=True):
        Client().deprecated_api()
    assert [w.category for w in recwarn] == [FutureWarning]


def test_quiet_deprecations_setting(monkeypatch):
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    monkeypatch.setattr(MAPI_CLIENT_SETTINGS, "QUIET", True)
    monkeypatch.setattr(MAPI_CLIENT_SETTINGS, "QUIET_DEPRECATIONS", True)
    display._configure_from_settings()
    assert display.is_quiet() and display._QUIET.deprecations


def test_client_deprecations_use_the_helper():
    """No direct FutureWarning in client code, so `quiet(deprecations=True)` covers all."""
    import pathlib

    import mp_api.client

    root = pathlib.Path(mp_api.client.__file__).parent
    offenders = [
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if path.name not in {"_display.py", "_external.py", "settings.py"}
        and "FutureWarning" in path.read_text()
    ]
    assert offenders == []


# --- the reported case ---------------------------------------------------------


def test_get_stability_quiet_silences_pymatgen_warnings(monkeypatch, capsys, records):
    """`with quiet(): mpr.get_stability(...)` printed pymatgen's per-entry warnings."""
    from pymatgen.analysis.phase_diagram import PhaseDiagram
    from pymatgen.entries.computed_entries import ComputedEntry

    from mp_api.client import MPRester
    from mp_api.client.core.client import _Rester
    from mp_api.client.routes.materials.thermo import ThermoRester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    refs = [
        ComputedEntry("Li", -1.9, entry_id="mp-1"),
        ComputedEntry("O2", -9.8, entry_id="mp-2"),
        ComputedEntry("Li2O", -14.0, entry_id="mp-3"),
    ]
    monkeypatch.setattr(
        ThermoRester,
        "get_phase_diagram_from_chemsys",
        lambda self, *a, **k: PhaseDiagram(refs),
    )
    # A correction scheme living in pymatgen that warns per entry with
    # `stacklevel=2`, like the mixing scheme's "Discarding r2SCAN entry ...".
    module = types.ModuleType("pymatgen.analysis.compatibility.fake")
    module.__file__ = "/site-packages/pymatgen/analysis/compatibility/fake.py"
    exec(
        compile(
            "import warnings\n"
            "from pymatgen.entries.compatibility import Compatibility\n"
            "class Scheme(Compatibility):\n"
            "    def get_adjustments(self, entry):\n"
            "        return []\n"
            "    def process_entries(self, entries, **kwargs):\n"
            "        for e in entries:\n"
            "            warnings.warn(f'WARNING! Discarding entry {e.entry_id}', stacklevel=2)\n"
            "        return list(entries)\n",
            module.__file__,
            "exec",
        ),
        module.__dict__,
    )
    monkeypatch.setattr(
        "pymatgen.entries.compatibility.MaterialsProject2020Compatibility",
        module.Scheme,
    )
    mine = [ComputedEntry("Li2O2", -24.0, entry_id="mine-1")]
    mpr = MPRester(api_key="a" * 32, mute_progress_bars=True)

    with warnings.catch_warnings():
        warnings.simplefilter("always")
        with quiet():
            assert mpr.get_stability(mine, thermo_type="GGA_GGA+U")
        assert not records and capsys.readouterr().err == ""

        mpr.get_stability(mine, thermo_type="GGA_GGA+U")  # not quiet
    assert len(records) == 4
    assert {r.name for r in records} == {f"{EXTERNAL_LOGGER}.pymatgen"}
    assert records[0].mp_message == "WARNING! Discarding entry mine-1"
    assert records[0].mp_origin == "pymatgen/analysis/compatibility/fake.py:8"


# --- the client's own warnings ---------------------------------------------------


@pytest.fixture
def default_printer(monkeypatch):
    """Python's default warning printing, with what it would print collected.

    (pytest records warnings by replacing the printer, which the client
    rightly leaves alone, so the default setup is rebuilt here.)
    """
    printed: list[str] = []
    monkeypatch.setattr(
        warnings,
        "_showwarnmsg_impl",
        lambda msg: printed.append(f"{msg.category.__name__}: {msg.message}"),
    )
    monkeypatch.setattr(
        warnings, "showwarning", _WarningHook(warnings._showwarning_orig)
    )
    return printed


def own_warnings():
    Client().advise()
    Client().deprecated_api()


def test_own_warnings_styled_in_terminal(term, default_printer):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        own_warnings()
    raw = term.getvalue()
    lines = [line.rstrip() for line in plain(raw).splitlines()]
    here = os.path.relpath(__file__)
    assert lines[0].split() == ["MPRestWarning", "check", "your", "arguments"]
    assert lines[1].strip().startswith(f"{here}:")
    assert lines[1].index(here) == lines[0].index("check")  # message column
    assert lines[2].split() == ["FutureWarning", "use", "something", "else"]
    assert "\x1b[38;2;214;158;0mMPRestWarning" in raw
    assert "\x1b[38;2;214;158;0mFutureWarning" in raw
    assert "check your arguments" in raw  # message unstyled
    assert f"\x1b[38;2;122;122;122m{here}:" in raw
    assert default_printer == []  # not printed a second time


def test_own_warnings_plain_when_not_interactive(pipe, default_printer):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        own_warnings()
    assert pipe.getvalue() == ""
    assert default_printer == [
        "MPRestWarning: check your arguments",
        "FutureWarning: use something else",
    ]


def test_own_warnings_respect_filters(term, default_printer):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", MPRestWarning)
        warnings.simplefilter("error", FutureWarning)
        Client().advise()
        with pytest.raises(FutureWarning):
            Client().deprecated_api()
    assert term.getvalue() == ""


def test_own_warnings_shown_once_per_location_by_default(term, default_printer):
    with warnings.catch_warnings():
        warnings.simplefilter("default")
        for _ in range(3):
            Client().advise()
    assert plain(term.getvalue()).count("MPRestWarning") == 1


def test_own_warnings_go_to_an_app_hook_below_ours(term, monkeypatch):
    """E.g. `logging.captureWarnings(True)` before importing the client."""
    seen = []
    monkeypatch.setattr(
        warnings, "showwarning", _WarningHook(lambda m, c, *a, **k: seen.append(c))
    )
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        own_warnings()
    assert seen == [MPRestWarning, FutureWarning]
    assert term.getvalue() == ""


def test_own_warnings_recorded_by_pytest(term):
    with pytest.warns(MPRestWarning, match="check your arguments"):
        Client().advise()
    assert term.getvalue() == ""


def test_user_warnings_are_not_styled(term, default_printer):
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.warn("user's own", FutureWarning)
    assert term.getvalue() == ""
    assert default_printer == ["FutureWarning: user's own"]


def test_quiet_silences_dataset_warnings(tmp_path):
    import pyarrow as pa
    from deltalake import write_deltalake

    from mp_api.client.core.exceptions import (
        MPDatasetIndexingWarning,
        MPDatasetIterationWarning,
        MPDatasetSlicingWarning,
    )
    from mp_api.client.core.utils import MPDataset

    write_deltalake(str(tmp_path), pa.table({"x": [1, 2, 3]}))
    dataset = MPDataset(str(tmp_path), document_model=None, use_document_model=False)
    with pytest.warns(MPDatasetIndexingWarning) as record:
        assert dataset[0] == {"x": 1}
    assert record[0].filename == __file__
    with pytest.warns(MPDatasetSlicingWarning):
        dataset[0:2]
    with pytest.warns(MPDatasetIterationWarning):
        list(dataset)

    with warnings.catch_warnings(record=True) as caught, quiet():
        warnings.simplefilter("always")
        dataset[0], dataset[0:2], list(dataset)
    assert caught == []
