"""Terminal / notebook output for the client: theme, progress bars and logging.

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

Opt out with `MPRESTER_LOGGING=false` or `mp_api.client.disable_logging()`.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

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
from rich.table import Column
from rich.text import Text
from rich.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from rich.console import RenderableType
    from rich.progress import Task

__all__ = [
    "MP_THEME",
    "disable_logging",
    "enable_logging",
    "get_console",
    "print_notice",
    "progress_bar",
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
    ) -> None:
        self.completed: float = 0
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

    Yields:
        ProgressHandle
    """
    console = get_console()
    if not enabled or not _is_interactive(console):
        yield ProgressHandle(total)
        return

    outermost = _STATE.depth() == 0
    _STATE.local.depth = _STATE.depth() + 1
    try:
        if not _can_draw_live(console):
            # e.g. Jupyter without ipywidgets: no live bar, still summarize
            handle = ProgressHandle(total)
            handle.shown = delay <= 0
            yield handle
        else:
            progress = _STATE.acquire(console)
            task_id = progress.add_task(
                description, total=total, visible=delay <= 0, unit=unit
            )
            handle = ProgressHandle(total, progress, task_id, delay)
            try:
                yield handle
            finally:
                _STATE.release(task_id)
    finally:
        _STATE.local.depth -= 1

    if summary and outermost and handle.shown and handle.completed:
        message = summary.format(
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
# Logging
# --------------------------------------------------------------------------

_PLAIN_FORMAT = "%(name)s - %(levelname)s - %(message)s"


@contextmanager
def status(
    message: str,
    *,
    enabled: bool = True,
    logger: logging.Logger | None = None,
) -> Iterator[None]:
    """Show a transient status line while a slow step runs.

    In a terminal or notebook with a live display, an amber spinner line is
    shown and removed when the block exits. Otherwise (logs, CI, or
    `enabled=False`), `message` is logged once as a warning via `logger`,
    since a log line can't be taken back.

    Args:
        message (str) : what is happening, e.g. "Counting documents..."
        enabled (bool) : if False, skip the spinner and only log
        logger (logging.Logger or None) : logger for the fallback warning.
            Nothing is logged if None.
    """
    console = get_console()
    if not (enabled and _is_interactive(console) and _can_draw_live(console)):
        if logger is not None:
            logger.warning(message)
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


def enable_logging(level: int | str | None = None) -> None:
    """Show messages from the client on stderr (the default).

    Safe to call repeatedly; only one handler is ever installed.

    Args:
        level (int, str or None) : minimum level to show, e.g. "WARNING".
            Defaults to the `MPRESTER_LOG_LEVEL` setting (INFO).
    """
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    logger = logging.getLogger(LOGGER_NAME)
    with _handler_lock:
        if _installed_handler(logger) is None:
            # Remove the placeholder NullHandler, if any
            for h in [h for h in logger.handlers if type(h) is logging.NullHandler]:
                logger.removeHandler(h)
            logger.addHandler(_MPDefaultHandler(logger))
            # The handler forwards to the application's handlers itself
            logger.propagate = False
        logger.setLevel(level or MAPI_CLIENT_SETTINGS.LOG_LEVEL)


def disable_logging() -> None:
    """Stop the client printing messages; standard logging propagation resumes."""
    logger = logging.getLogger(LOGGER_NAME)
    with _handler_lock:
        if (handler := _installed_handler(logger)) is not None:
            logger.removeHandler(handler)
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


def _install_default_logging() -> None:
    """Install the default handler on import, unless disabled by settings."""
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    if MAPI_CLIENT_SETTINGS.LOGGING:
        enable_logging()
    else:
        logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())
