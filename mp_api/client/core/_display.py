"""Terminal / notebook output for the client: theme, progress bars, logging, quiet mode.

All output goes to a single `rich.console.Console` writing to **stderr**,
so stdout stays clean (required by e.g. the MCP server's stdio transport).

Progress bars
-------------
`progress_bar(...)` is a context manager. Every bar in the process is a task
on one shared `rich.progress.Progress`, because rich allows only one live
display at a time. Nested bars (e.g. batched queries that paginate) and bars
opened from several threads are supported. A bar is always removed when its
`with` block exits, including on exceptions.

Bars are only drawn in an interactive terminal or Jupyter (with ipywidgets
installed). Elsewhere (web servers, CI, pipes) nothing is drawn or printed.

Logging
-------
A default handler is attached to the `mp_api.client` logger on import, so
users see the client's messages without configuring logging. It writes
themed output in a terminal / notebook and plain one-line records otherwise.

If the application has configured logging (handlers on the root logger, or on
any ancestor of `mp_api.client`), records are passed to those handlers
instead, honouring the application's levels, so nothing is printed twice.

Configuration has a single owner: only the `mp_api.client` logger is given a
level, handler or propagation setting, here. Child loggers (`mp_api.client.*`,
including contribs) never set their own level, so one setting controls all of
them. Use `MPRESTER_LOG_LEVEL` or `enable_logging(level)`.

Quiet mode
----------
`quiet()` (or `MPRESTER_QUIET=true`, or `MPRester(quiet=True)`) silences the
client for the whole process: no log records, progress bars, status lines,
notices or `MPRestWarning`s. Deprecation warnings (`FutureWarning`) and
exceptions are still raised. It can be used as a context manager.

Which channel to use
--------------------
- The operation failed: raise an exception.
- A deprecated API was used: `warnings.warn(..., FutureWarning)`, which is
  shown by default, also when called from other libraries.
- Something the caller can change in their call (an ignored argument, misuse,
  a caveat about what the data means): `mp_warning(...)` (an `MPRestWarning`).
- A runtime or data event the caller can't change in code (server
  unreachable, data missing, a local dataset reused): `logger.warning/info`.
- Diagnostics: `logger.debug`.
- Transient progress: `progress_bar` / `status`, interactive output only.
- Output the user explicitly asked for (`notify_db_version`): `print_notice`.

So WARNING-level log records always mean something went wrong, and
`MPRestWarning` / `FutureWarning` always mean the caller can fix something.

Using mp-api in an application
------------------------------
E.g. a web server that wants to know about problems and misuse, but no
progress output:

```python
import logging

logging.basicConfig(level=logging.WARNING)  # or the app's own logging config
logging.captureWarnings(True)  # MPRestWarning / FutureWarning into the logs

from mp_api.client import MPRester

mpr = MPRester(mute_progress_bars=True)  # or MPRESTER_MUTE_PROGRESS_BARS=true
```

Client log records go to the application's handlers, at its levels. Without
an application logging config, set `MPRESTER_LOG_LEVEL=WARNING` instead.
Python shows a given warning once per code location; use
`warnings.simplefilter("always", MPRestWarning)` to see every occurrence, or
`"error"` (e.g. in the application's tests) to fail on misuse.
"""

from __future__ import annotations

import io
import logging
import threading
import time
import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Self

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner
from rich.table import Column, Table
from rich.text import Text
from rich.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Any, Literal

    from rich.console import RenderableType
    from rich.progress import Task

__all__ = [
    "MP_THEME",
    "DatabaseVersions",
    "enable_logging",
    "get_console",
    "is_quiet",
    "mp_warning",
    "print_notice",
    "progress_bar",
    "quiet",
    "set_console",
    "status",
]

LOGGER_NAME = "mp_api.client"

MP_THEME = Theme(
    {
        "mp.brand": "#00BDAD",  # $primary (MP teal)
        "mp.brand.dark": "#008F83",  # $primary-dark
        "mp.accent": "#3960E3",  # $tertiary (links)
        "mp.secondary": "#939FC8",  # $secondary-light (readable on dark bg)
        "mp.success": "#48C78E",  # Bulma success
        "mp.warning": "#D69E00",  # amber, readable on light + dark bg
        "mp.error": "#F14668",  # Bulma danger
        "mp.muted": "#7A7A7A",  # Bulma .has-text-grey
        "mp.title": "bold underline",
        "mp.field": "bold",
        "mp.table.header": "bold #008F83",  # brand dark
        # database versions, relative to the one the API serves
        "mp.version.current": "bold #48C78E",  # success green
        "mp.version.newer": "#3960E3",  # accent blue
        "mp.version.older": "#7A7A7A",  # muted grey
        # rich built-ins used by progress bars / logging
        "progress.description": "default",
        "progress.download": "#939FC8",
        "progress.elapsed": "#7A7A7A",
        "progress.remaining": "#7A7A7A",
        "progress.spinner": "#00BDAD",
        "bar.complete": "#00BDAD",
        "bar.finished": "#008F83",
        "bar.pulse": "#00BDAD",
        "logging.level.info": "#00BDAD",
        "logging.level.warning": "#D69E00",
        "logging.level.error": "#F14668",
        "logging.level.critical": "bold reverse #F14668",
        "logging.level.debug": "#7A7A7A",
    }
)

# --------------------------------------------------------------------------
# Console
# --------------------------------------------------------------------------


class _ConsoleHolder:
    console: Console | None = None
    lock = threading.Lock()


def get_console() -> Console:
    """Get the shared console (stderr, MP theme), creating it on first use."""
    if _ConsoleHolder.console is None:
        with _ConsoleHolder.lock:
            if _ConsoleHolder.console is None:
                _ConsoleHolder.console = Console(stderr=True, theme=MP_THEME)
    return _ConsoleHolder.console


def set_console(console: Console | None) -> None:
    """Replace the shared console, e.g. in tests. `None` resets to the default."""
    with _ConsoleHolder.lock:
        _ConsoleHolder.console = console


def _is_interactive(console: Console) -> bool:
    return console.is_jupyter or (console.is_terminal and not console.is_dumb_terminal)


def _can_draw_live(console: Console) -> bool:
    """Whether live progress can be drawn (needs ipywidgets under Jupyter)."""
    if console.is_jupyter:
        try:
            import ipywidgets  # noqa: F401
        except ImportError:
            return False
        return True
    return console.is_terminal and not console.is_dumb_terminal


def print_notice(message: str, style: str | None = None) -> None:
    """Print a one-line notice to the console (stderr).

    Plain text: the message is not parsed for rich markup.

    Args:
        message (str) : text to print
        style (str or None) : theme style, e.g. "mp.warning"
    """
    if is_quiet():
        return
    get_console().print(Text(message, style=style or ""))


# --------------------------------------------------------------------------
# Progress bars
# --------------------------------------------------------------------------


class _RateColumn(ProgressColumn):
    """Items per second, using the task's `unit` field. Hidden on narrow terminals."""

    min_console_width = 100

    def render(self, task: Task) -> Text:
        console = get_console()
        if console.width < self.min_console_width:
            return Text("")
        speed = task.finished_speed or task.speed
        if speed is None:
            return Text("")
        unit = task.fields.get("unit", "it")
        if speed >= 1000:
            return Text(f"{speed / 1000:.1f}k {unit}/s", style="mp.secondary")
        return Text(f"{speed:.0f} {unit}/s", style="mp.secondary")


class _MPProgress(Progress):
    """Progress that draws status tasks (see `status`) as full-width lines.

    Status lines are shown above the bars, so long messages aren't cut to
    the width of the bar table's description column.
    """

    _spinner = Spinner("dots", style="progress.spinner")

    def get_renderables(self) -> Iterable[RenderableType]:
        statuses = [t for t in self.tasks if t.fields.get("status") and t.visible]
        bars = [t for t in self.tasks if not t.fields.get("status")]
        for task in statuses:
            spinner = self._spinner.render(self.get_time())
            yield Text.assemble(
                spinner if isinstance(spinner, Text) else Text(str(spinner)),
                " ",
                Text(task.description, style="mp.warning"),
                " ",
                Text(f"({int(task.elapsed or 0)}s)", style="progress.elapsed"),
                overflow="fold",
            )
        if bars:
            yield self.make_tasks_table(bars)


class _ProgressState:
    """The process-wide Progress and its reference count. Guarded by `lock`."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.progress: Progress | None = None
        self.active = 0
        self.local = threading.local()  # per-thread nesting depth

    def depth(self) -> int:
        return getattr(self.local, "depth", 0)

    def acquire(self, console: Console) -> Progress:
        with self.lock:
            if self.progress is None:
                self.progress = _MPProgress(
                    SpinnerColumn(),
                    # The description is truncated (with an ellipsis) to leave
                    # room for the numbers on narrow terminals.
                    TextColumn(
                        "{task.description}",
                        table_column=Column(
                            no_wrap=True,
                            overflow="ellipsis",
                            max_width=max(20, console.width * 2 // 5),
                        ),
                    ),
                    BarColumn(bar_width=20),
                    MofNCompleteColumn(table_column=Column(no_wrap=True)),
                    _RateColumn(table_column=Column(no_wrap=True)),
                    TimeElapsedColumn(table_column=Column(no_wrap=True)),
                    TimeRemainingColumn(table_column=Column(no_wrap=True)),
                    console=console,
                    transient=True,
                )
                self.progress.start()
            self.active += 1
            return self.progress

    def release(self, task_id: TaskID) -> None:
        with self.lock:
            if self.progress is None:  # pragma: no cover - defensive
                return
            self.progress.remove_task(task_id)
            self.active -= 1
            if self.active == 0:
                self.progress.stop()
                self.progress = None


_STATE = _ProgressState()


class ProgressHandle:
    """Handle yielded by `progress_bar`; update it as work completes."""

    def __init__(
        self,
        total: float | None,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
        delay: float = 0.0,
        summary: str | None = None,
    ) -> None:
        self.completed: float = 0
        #: completion line, formatted as in `progress_bar`; can be changed while the
        #: bar runs, e.g. to report results that are only known at the end
        self.summary = summary
        self._total = total
        self._progress = progress
        self._task_id = task_id
        self._delay = delay
        self._start = time.monotonic()
        self.shown = progress is not None and delay <= 0

    @property
    def total(self) -> float | None:
        return self._total

    @total.setter
    def total(self, value: float | None) -> None:
        self._total = value
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, total=value)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start

    def hide(self) -> None:
        """Remove the bar from the display, e.g. before a final slow step.

        The summary (if any) is still printed when the `progress_bar`
        block exits, and later updates are counted but not drawn.
        """
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, visible=False)
        self._delay = float("inf")  # don't show it again on update

    def update(self, advance: float = 1) -> None:
        """Advance the bar by `advance` units."""
        self.completed += advance
        if self._progress is None or self._task_id is None:
            return
        if not self.shown and self.elapsed >= self._delay:
            self.shown = True
            self._progress.update(self._task_id, visible=True)
        self._progress.advance(self._task_id, advance)


def _as_int(value: float | None) -> float | None:
    """Show (near) whole-number counts as ints, without a trailing `.0`."""
    if isinstance(value, float) and abs(value - round(value)) < 1e-6:
        return int(round(value))
    return value


@contextmanager
def progress_bar(
    description: str,
    total: float | None = None,
    *,
    enabled: bool = True,
    delay: float = 0.0,
    unit: str = "docs",
    summary: str | None = None,
    log: str | None = None,
) -> Iterator[ProgressHandle]:
    """Show a progress bar for the duration of a `with` block.

    Args:
        description (str) : label shown next to the bar
        total (float or None) : expected number of units, None if unknown
        enabled (bool) : if False, nothing is shown (a no-op handle is yielded)
        delay (float) : seconds before the bar is shown, so quick
            operations stay silent. Checked on each update.
        unit (str) : unit name for the rate column
        summary (str or None) : if given, printed as a one-line summary when
            the outermost bar on this thread finishes without error, was
            shown, and completed at least one unit. Formatted with `completed` and `total`, and followed by
            the elapsed time, e.g. "Retrieved {completed:,} documents".
            Can be replaced through `ProgressHandle.summary` inside the block.
        log (str or None) : if given, logged once at INFO when progress is
            enabled but no live bar can be drawn (scripts, servers, CI, Jupyter
            without ipywidgets), as `status` does. Not logged when disabled or
            in quiet mode.

    Yields:
        ProgressHandle
    """
    console = get_console()
    if not enabled or is_quiet():
        yield ProgressHandle(total, summary=summary)
        return
    if not _is_interactive(console):
        if log:
            logging.getLogger(LOGGER_NAME).info(log)
        yield ProgressHandle(total, summary=summary)
        return

    outermost = _STATE.depth() == 0
    _STATE.local.depth = _STATE.depth() + 1
    try:
        if not _can_draw_live(console):
            # e.g. Jupyter without ipywidgets: no live bar, still summarize
            if log:
                logging.getLogger(LOGGER_NAME).info(log)
            handle = ProgressHandle(total, summary=summary)
            handle.shown = delay <= 0
            yield handle
        else:
            progress = _STATE.acquire(console)
            task_id = progress.add_task(
                description, total=total, visible=delay <= 0, unit=unit
            )
            handle = ProgressHandle(total, progress, task_id, delay, summary)
            try:
                yield handle
            finally:
                _STATE.release(task_id)
    finally:
        _STATE.local.depth -= 1

    if handle.summary and outermost and handle.shown and handle.completed:
        message = handle.summary.format(
            completed=_as_int(handle.completed), total=_as_int(handle.total)
        )
        console.print(
            Text.assemble(
                ("✓ ", "mp.brand"),
                message,
                (f" in {handle.elapsed:.1f}s", "mp.muted"),
            )
        )


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------


class DatabaseVersions(dict[str, list[str]]):
    """Database versions per dataset: a plain `dict` that displays as a table.

    Behaves exactly like `dict[str, list[str]]` (indexing, iteration,
    equality, JSON). Only its representation differs: evaluating it in a REPL
    or notebook shows a table. Versions are coloured relative to the one the
    API serves: that one green and marked `*`, newer ones blue, older ones grey.
    """

    def __init__(
        self, versions: dict[str, list[str]], current: str | None = None
    ) -> None:
        """Create the mapping.

        Args:
            versions (dict of str to list of str) : dataset name to versions
            current (str or None) : version the API serves, marked in the table
        """
        super().__init__(versions)
        self.current = current

    def _style(self, version: str) -> str:
        """Theme style for a version, relative to the version the API serves."""
        if not self.current:
            return ""
        if version == self.current:
            return "mp.version.current"
        # Versions are dates (with optional -postN suffixes), so they sort as text
        return "mp.version.newer" if version > self.current else "mp.version.older"

    def _legend(self, styled: bool) -> Text | None:
        """Caption explaining the markers / colours present in the table."""
        if not self.current:
            return None
        seen = {self._style(v) for versions in self.values() for v in versions}
        parts: list[str | tuple[str, str]] = []
        if "mp.version.current" in seen:
            parts += [(f"{self.current}*", "mp.version.current"), " served by the API"]
        if styled and "mp.version.newer" in seen:
            parts += ["  ", ("newer", "mp.version.newer")]
        if styled and "mp.version.older" in seen:
            parts += ["  ", ("older", "mp.version.older")]
        return Text.assemble(*parts) if parts else None

    def _table(self, styled: bool) -> Table:
        def st(style: str) -> str:
            return style if styled else ""

        table = Table(
            title="Database versions available on S3",
            title_style=st("bold"),
            header_style=st("mp.table.header"),
            border_style=st("mp.muted"),
            caption=self._legend(styled),
            caption_style=st("mp.muted"),
        )
        # default foreground: white on dark terminals, still readable on light ones
        table.add_column("Dataset", no_wrap=True)
        table.add_column("Versions")
        for name, versions in self.items():
            cells = [
                Text(
                    f"{v}*" if v == self.current else v,
                    style=st(self._style(v)),
                )
                for v in versions
            ]
            table.add_row(name, Text(", ").join(cells))
        return table

    def _render(self, color: bool, width: int = 200) -> str:
        """The table as text, with ANSI colours if `color`."""
        buf = io.StringIO()
        Console(
            file=buf,
            width=width,
            theme=MP_THEME,
            force_terminal=color,
            color_system=_color_system() if color else None,
            force_jupyter=False,
        ).print(self._table(styled=color))
        return buf.getvalue().rstrip("\n")

    def __rich__(self) -> Table:
        return self._table(styled=True)

    def __repr__(self) -> str:
        """The table. Coloured only in an interactive session on a colour
        terminal, so a repr in logs or files never contains ANSI codes.
        """
        if not self:
            return "DatabaseVersions({})"
        if _interactive_color():
            return self._render(color=True, width=get_console().width)
        return self._render(color=False)

    def __str__(self) -> str:
        return self._render(color=False) if self else "DatabaseVersions({})"

    def _repr_pretty_(self, p: Any, cycle: bool) -> None:
        """IPython terminal: the table (IPython would otherwise pretty-print a dict)."""
        p.text(self.__repr__())

    def _repr_html_(self) -> str:
        """Jupyter: the styled table."""
        console = Console(
            file=io.StringIO(),
            record=True,
            width=200,
            theme=MP_THEME,
            force_jupyter=False,
        )
        console.print(self._table(styled=True))
        return console.export_html(inline_styles=True, code_format="<pre>{code}</pre>")


def _color_system() -> Literal["standard", "256", "truecolor"]:
    """Colour depth of the user's terminal, for reprs rendered to a string."""
    detected = get_console().color_system
    if detected == "truecolor":
        return "truecolor"
    return "256" if detected == "256" else "standard"


def _interactive_color() -> bool:
    """Whether a repr may contain colours: an interactive Python/IPython session
    whose stdout is a colour terminal, and NO_COLOR isn't set.
    """
    import os
    import sys

    interactive = hasattr(sys, "ps1") or bool(sys.flags.interactive)
    try:
        from IPython import get_ipython  # type: ignore[attr-defined]

        shell = get_ipython()
        interactive = interactive or (
            shell is not None and type(shell).__name__ == "TerminalInteractiveShell"
        )
    except ImportError:
        pass
    return (
        interactive
        and sys.stdout is not None
        and sys.stdout.isatty()
        and "NO_COLOR" not in os.environ
        and os.environ.get("TERM") != "dumb"
    )


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

_PLAIN_FORMAT = "%(name)s - %(levelname)s - %(message)s"


@contextmanager
def status(message: str, *, enabled: bool = True) -> Iterator[None]:
    """Show a transient status line while a slow step runs.

    In a terminal or notebook with a live display, an amber spinner line is
    shown and removed when the block exits. If progress output is enabled but
    can't be drawn live (logs, CI, Jupyter without ipywidgets), `message` is
    logged once at INFO instead (it's progress, not a problem, so it stays out
    of WARNING-level logs). If disabled (muted progress bars) or in quiet mode,
    nothing is shown or logged.

    Args:
        message (str) : what is happening, e.g. "Counting documents..."
        enabled (bool) : if False, show nothing
    """
    console = get_console()
    if not enabled or is_quiet():
        yield
        return
    if not (_is_interactive(console) and _can_draw_live(console)):
        logging.getLogger(LOGGER_NAME).info(message)
        yield
        return

    progress = _STATE.acquire(console)
    task_id = progress.add_task(message, total=None, status=True)
    try:
        yield
    finally:
        _STATE.release(task_id)


def _app_handlers(logger: logging.Logger) -> list[logging.Handler]:
    """Handlers the application attached to ancestors of `logger`."""
    handlers: list[logging.Handler] = []
    current = logger.parent
    while current is not None:
        handlers.extend(current.handlers)
        if not current.propagate:
            break
        current = current.parent
    return handlers


def _app_level(logger: logging.Logger) -> int:
    """Effective level the application set above `logger`."""
    current = logger.parent
    while current is not None:
        if current.level:
            return current.level
        current = current.parent
    return logging.WARNING  # pragma: no cover - root always has a level


class _MPDefaultHandler(logging.Handler):
    """Default handler for `mp_api.client`, see module docstring."""

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__()
        self._logger = logger
        self._rich: RichHandler | None = None
        self._plain = logging.Formatter(_PLAIN_FORMAT)

    def _rich_handler(self, console: Console) -> RichHandler:
        if self._rich is None or self._rich.console is not console:
            self._rich = RichHandler(
                console=console,
                show_time=False,
                show_path=False,
                markup=False,
                rich_tracebacks=False,
            )
        return self._rich

    def emit(self, record: logging.LogRecord) -> None:
        # Defer to logging the application configured, with its levels.
        # (`mp_api.client` doesn't propagate while this handler is installed.)
        if handlers := _app_handlers(self._logger):
            if record.levelno >= _app_level(self._logger):
                for handler in handlers:
                    if record.levelno >= handler.level:
                        handler.handle(record)
            return

        try:
            console = get_console()
            if _is_interactive(console):
                self._rich_handler(console).emit(record)
            else:
                console.file.write(self._plain.format(record) + "\n")
                console.file.flush()
        except Exception:  # pragma: no cover - logging must not raise
            self.handleError(record)


_handler_lock = threading.Lock()


def _installed_handler(logger: logging.Logger) -> _MPDefaultHandler | None:
    return next((h for h in logger.handlers if isinstance(h, _MPDefaultHandler)), None)


def _parse_level(level: int | str) -> int:
    """Log level as an int, from an int or a name like "warning"."""
    if isinstance(level, int):
        return level
    try:
        return logging.getLevelNamesMapping()[level.strip().upper()]
    except KeyError:
        raise ValueError(f"Unknown log level {level!r}") from None


def enable_logging(level: int | str | None = None) -> None:
    """Show messages from the client on stderr (the default), at `level`.

    Safe to call repeatedly; only one handler is ever installed. In quiet
    mode the level is remembered and applied when quiet mode ends.

    Args:
        level (int, str or None) : minimum level to show, e.g. "WARNING".
            Defaults to the `MPRESTER_LOG_LEVEL` setting (INFO).
    """
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    logger = logging.getLogger(LOGGER_NAME)
    level = _parse_level(level or MAPI_CLIENT_SETTINGS.LOG_LEVEL)
    with _handler_lock:
        if _installed_handler(logger) is None:
            logger.addHandler(_MPDefaultHandler(logger))
            # The handler forwards to the application's handlers itself
            logger.propagate = False
        if _QUIET.enabled:
            _QUIET.saved_level = level
        else:
            logger.setLevel(level)


# --------------------------------------------------------------------------
# Quiet mode
# --------------------------------------------------------------------------

# Above CRITICAL: every record from mp_api.client (and its children, which
# never set their own level) is dropped before reaching any handler.
_SILENT = logging.CRITICAL + 1


class _QuietState:
    """Process-wide quiet flag. `saved_level` is the log level to restore."""

    def __init__(self) -> None:
        self.enabled = False
        self.saved_level: int = logging.NOTSET


_QUIET = _QuietState()


class _QuietContext:
    """Returned by `quiet()`; restores the previous state when used with `with`."""

    def __init__(self, previous: bool) -> None:
        self._previous = previous

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        _set_quiet(self._previous)


def _set_quiet(enabled: bool) -> bool:
    """Turn quiet mode on or off, returning the previous state."""
    logger = logging.getLogger(LOGGER_NAME)
    with _handler_lock:
        previous = _QUIET.enabled
        if enabled and not previous:
            _QUIET.saved_level = logger.level
            logger.setLevel(_SILENT)
        elif previous and not enabled:
            logger.setLevel(_QUIET.saved_level)
        _QUIET.enabled = enabled
    return previous


def quiet(enabled: bool = True) -> _QuietContext:
    """Silence all output from the client in this process.

    While quiet, the client emits no log records (they don't reach the
    application's handlers either), progress bars, status lines, notices or
    `MPRestWarning`s. Deprecation warnings and exceptions are unaffected.

    Takes effect immediately; as a context manager, the previous state is
    restored on exit:

    ```python
    from mp_api.client import quiet

    quiet()  # for the rest of the process
    with quiet():  # only within the block
        ...
    ```

    Args:
        enabled (bool) : True to silence the client, False to restore output.

    Returns:
        a context manager that restores the previous state on exit
    """
    return _QuietContext(_set_quiet(enabled))


def is_quiet() -> bool:
    """Whether quiet mode is on, see `quiet()`."""
    return _QUIET.enabled


def mp_warning(message: str, stacklevel: int = 1) -> None:
    """Emit an `MPRestWarning`, unless in quiet mode.

    For things the caller can change in their call, see the module docstring.

    Args:
        message (str) : warning text
        stacklevel (int) : as for `warnings.warn`, relative to the caller
    """
    if _QUIET.enabled:
        return
    from mp_api.client.core.exceptions import MPRestWarning

    warnings.warn(message, MPRestWarning, stacklevel=stacklevel + 1)


def _configure_from_settings() -> None:
    """Configure client output from settings, on import of `mp_api.client`."""
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    enable_logging()
    if MAPI_CLIENT_SETTINGS.QUIET:
        quiet(True)
