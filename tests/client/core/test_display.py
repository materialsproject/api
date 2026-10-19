"""Tests for progress bars, the shared console, and default logging.

Uses consoles writing to StringIO; no network access or API key needed.
"""

import io
import re
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client.core._display import (
    MP_THEME,
    enable_logging,
    get_console,
    print_notice,
    progress_bar,
    set_console,
)


def _console(terminal: bool = True) -> tuple[Console, io.StringIO]:
    buf = io.StringIO()
    console = Console(
        file=buf,
        force_terminal=terminal,
        force_jupyter=False,
        theme=MP_THEME,
        width=120,
        color_system="truecolor" if terminal else None,
    )
    return console, buf


@pytest.fixture
def term():
    console, buf = _console(terminal=True)
    set_console(console)
    yield buf
    set_console(None)


@pytest.fixture
def pipe():
    console, buf = _console(terminal=False)
    set_console(console)
    yield buf
    set_console(None)


@pytest.fixture
def no_root_handlers(monkeypatch):
    """Simulate an application that hasn't configured logging.

    (pytest's logging plugin attaches handlers to the root logger during each
    test, which the default handler would correctly defer to.)
    """
    monkeypatch.setattr(display, "_app_handlers", lambda logger: [])
    enable_logging()
    yield
    enable_logging()


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


# --- console -------------------------------------------------------------------


def test_default_console_writes_to_stderr(capsys):
    set_console(None)
    try:
        console = get_console()
        assert console.stderr
        print_notice("hello stderr")
        out, err = capsys.readouterr()
        assert out == ""
        assert "hello stderr" in err
    finally:
        set_console(None)


def test_print_notice_is_not_markup(term):
    print_notice("[bold]literal[/bold]")
    assert "[bold]literal[/bold]" in term.getvalue()


def test_theme_colours():
    styles = MP_THEME.styles
    assert str(styles["mp.brand"].color.triplet.hex) == "#00bdad"
    assert str(styles["mp.warning"].color.triplet.hex) == "#d69e00"


# --- progress bars -------------------------------------------------------------


def test_disabled_bar_is_silent(term):
    with progress_bar("x", total=3, enabled=False, summary="Done {completed}") as bar:
        bar.update(3)
    assert term.getvalue() == ""
    assert bar.completed == 3


def test_non_interactive_console_draws_nothing(pipe):
    with progress_bar("x", total=3, summary="Done {completed}") as bar:
        bar.update(3)
    assert pipe.getvalue() == ""
    assert display._STATE.progress is None


def test_summary_printed_for_completed_bar(term):
    with progress_bar(
        "Fetching", total=5, summary="Retrieved {completed:,} docs"
    ) as bar:
        bar.update(5)
    out = plain(term.getvalue())
    assert "✓ Retrieved 5 docs in" in out
    assert display._STATE.progress is None
    assert display._STATE.active == 0


def test_nested_bars_share_display_and_only_outer_summarizes(term):
    with progress_bar("outer", total=2, summary="outer done") as outer:
        assert display._STATE.active == 1
        progress = display._STATE.progress
        for _ in range(2):
            with progress_bar("inner", total=1, summary="inner done") as inner:
                # no LiveError: same Progress, extra task
                assert display._STATE.progress is progress
                assert display._STATE.active == 2
                inner.update(1)
            outer.update(1)
    out = term.getvalue()
    assert "outer done" in out
    assert "inner done" not in out
    assert display._STATE.progress is None


def test_bar_cleaned_up_on_exception(term):
    with pytest.raises(RuntimeError), progress_bar("x", total=2, summary="nope") as bar:
        bar.update(1)
        raise RuntimeError("boom")
    assert display._STATE.progress is None
    assert display._STATE.active == 0
    assert "nope" not in term.getvalue()
    assert display._STATE.depth() == 0


def test_delay_hides_quick_operations(term):
    with progress_bar("x", total=1, delay=60, summary="hidden") as bar:
        bar.update(1)
        assert not bar.shown
        task = display._STATE.progress.tasks[0]
        assert not task.visible
    assert "hidden" not in term.getvalue()


def test_delay_shows_after_elapsed(term, monkeypatch):
    with progress_bar("x", total=2, delay=5, summary="shown") as bar:
        monkeypatch.setattr(type(bar), "elapsed", property(lambda self: 10.0))
        bar.update(1)
        assert bar.shown
        assert display._STATE.progress.tasks[0].visible
    assert "shown" in term.getvalue()


def test_total_can_be_changed(term):
    with progress_bar("x", total=None) as bar:
        bar.total = 10
        assert display._STATE.progress.tasks[0].total == 10


def test_concurrent_bars_from_threads(term):
    def work(i):
        with progress_bar(f"t{i}", total=10, summary=f"thread {i} done") as bar:
            for _ in range(10):
                bar.update(1)
        return i

    with ThreadPoolExecutor(4) as pool:
        assert sorted(pool.map(work, range(8))) == list(range(8))

    out = term.getvalue()
    # each thread's bar is outermost on its own thread
    assert all(f"thread {i} done" in out for i in range(8))
    assert display._STATE.progress is None
    assert display._STATE.active == 0


def test_jupyter_without_ipywidgets_still_summarizes(monkeypatch, term):
    monkeypatch.setattr(display, "_can_draw_live", lambda console: False)
    with progress_bar("x", total=1, summary="nb done") as bar:
        bar.update(1)
    assert display._STATE.progress is None
    assert "nb done" in term.getvalue()


# --- logging -------------------------------------------------------------------


def _client_logger():
    return logging.getLogger("mp_api.client")


def _installed():
    return [
        h for h in _client_logger().handlers if isinstance(h, display._MPDefaultHandler)
    ]


def test_default_handler_installed_on_import():
    import mp_api.client  # noqa: F401

    assert len(_installed()) == 1
    assert not _client_logger().propagate


def test_enable_logging_is_idempotent():
    enable_logging()
    enable_logging("WARNING")
    try:
        assert len(_installed()) == 1
        assert _client_logger().level == logging.WARNING
    finally:
        enable_logging()


def test_enable_logging_rejects_unknown_level():
    with pytest.raises(ValueError, match="Unknown log level 'LOUD'"):
        enable_logging("LOUD")
    enable_logging("warning")  # case-insensitive
    try:
        assert _client_logger().level == logging.WARNING
    finally:
        enable_logging()


def test_logging_plain_when_not_a_terminal(pipe, no_root_handlers):
    logging.getLogger("mp_api.client.core.client").warning("dataset written")
    out = pipe.getvalue()
    assert out == "mp_api.client.core.client - WARNING - dataset written\n"


def test_logging_rich_in_terminal(term, no_root_handlers):
    logging.getLogger("mp_api.client.core.client").info("dataset written")
    out = term.getvalue()
    assert "dataset written" in out
    assert "INFO" in out
    assert "\x1b[" in out  # styled


def test_logging_level_respected(pipe, no_root_handlers):
    enable_logging("WARNING")
    logging.getLogger("mp_api.client.core.client").info("too quiet")
    assert pipe.getvalue() == ""


def test_defers_to_application_logging(pipe, monkeypatch):
    """With root handlers configured, records go there once, at the app's level."""
    root = logging.getLogger()
    app_buf = io.StringIO()
    app_handler = logging.StreamHandler(app_buf)
    monkeypatch.setattr(root, "handlers", [app_handler])
    monkeypatch.setattr(root, "level", logging.ERROR)
    enable_logging()

    log = logging.getLogger("mp_api.client.core.client")
    log.warning("below app level")
    log.error("app sees this")

    assert pipe.getvalue() == ""  # our console printed nothing
    assert app_buf.getvalue() == "app sees this\n"  # once, not duplicated


def test_contribs_logger_uses_shared_handler(pipe, no_root_handlers, capsys):
    pytest.importorskip("boltons")
    from mp_api.client.contribs._logger import MPCC_LOGGER

    assert MPCC_LOGGER.logger.handlers == []
    MPCC_LOGGER.info("project created")
    out, _ = capsys.readouterr()
    assert out == ""  # never stdout
    assert "mp_api.client.contribs - INFO - project created" in pipe.getvalue()


def test_logging_from_threads_during_progress(term, no_root_handlers):
    log = logging.getLogger("mp_api.client.core.delta")
    with progress_bar("x", total=4, summary="done") as bar:
        threads = [
            threading.Thread(target=lambda: (log.warning("refreshing"), bar.update(1)))
            for _ in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    out = term.getvalue()
    assert out.count("refreshing") == 4
    assert "done" in out


# --- notify_db_version ---------------------------------------------------------


def test_db_version_check_prints(term, monkeypatch, tmp_path):
    import warnings

    from mp_api.client.core.exceptions import MPRestWarning
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
    from mp_api.client.mprester import MPRester

    log_file = tmp_path / "mprester.log.yaml"
    monkeypatch.setattr(MAPI_CLIENT_SETTINGS, "LOG_FILE", log_file)

    class Fake:
        db_version = "2026.01.01"

    MPRester._db_version_check(Fake())  # first run: just the version
    assert "Materials Project database version: v2026.01.01" in plain(term.getvalue())

    Fake.db_version = "2026.02.01"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        MPRester._db_version_check(Fake())
    assert (
        "Materials Project database version changed: v2026.01.01 → v2026.02.01"
        in plain(term.getvalue())
    )
    assert any(issubclass(w.category, MPRestWarning) for w in caught)
    assert "2026.02.01" in log_file.read_text()
