"""Route output from other libraries through the client's logging, during client calls.

Libraries the client uses (pymatgen, emmet, pydantic, numpy, ...) report
problems with `warnings.warn`, or with `logging` on their own loggers. Left
alone, these bypass the client's output model: `quiet()` can't silence them,
and a library warning raised with `stacklevel=2` is reported at the client's
line that called the library, not at the library code that warned.

While a client call is running (`capturing()`, entered automatically by every
public method of the resters, `MPDataset` and `ContribsClient`):

- Library warnings become WARNING log records on
  `mp_api.client.external.<package>` (e.g. `mp_api.client.external.pymatgen`),
  one per warning, naming the library code that warned. Being children of
  `mp_api.client`, they follow `quiet()`, `MPRESTER_LOG_LEVEL` and the
  application's logging config, and can be tuned per library, e.g.
  `logging.getLogger("mp_api.client.external.pymatgen").setLevel(logging.ERROR)`.
- Library log records that would otherwise reach Python's fallback handler
  (`logging.lastResort`, used only when nothing has configured logging) are
  re-logged on the same loggers.

Not routed (passed through unchanged): deprecation warnings from libraries
(`DeprecationWarning`, `PendingDeprecationWarning`, `FutureWarning`), which
are about the client's use of a library.

The client's own warnings (anything raised from `mp_api` code, at any time)
stay Python warnings. When they would be printed by Python's default printer
to an interactive console, the same hook renders them in the client's style
instead (`_display.print_warning`).

Python's warning filters still apply first, so `"ignore"`, `"error"` and the
default once-per-location rule keep working. An application that replaces
`warnings.showwarning` itself (e.g. `logging.captureWarnings(True)` after
importing the client, or `warnings.catch_warnings(record=True)` as used by
`pytest.warns`) gets every warning, and the client doesn't take the hook back.
"""

from __future__ import annotations

import contextvars
import functools
import inspect
import logging
import sys
import threading
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import FrameType
    from typing import Any, TextIO, TypeVar

    T = TypeVar("T")

EXTERNAL_LOGGER = "mp_api.client.external"

_THIS_FILE = __file__

# Methods wrapped besides public ones (no leading underscore)
_WRAPPED_DUNDERS = frozenset({"__init__", "__getitem__"})

_PASS_THROUGH_CATEGORIES: tuple[type[Warning], ...] = (
    DeprecationWarning,
    PendingDeprecationWarning,
    FutureWarning,
)

_WARNINGS_MODULES = frozenset({"warnings", "_py_warnings", __name__})

_depth: contextvars.ContextVar[int] = contextvars.ContextVar(
    "mp_api_client_call_depth", default=0
)


# --------------------------------------------------------------------------
# Marking client calls
# --------------------------------------------------------------------------


@contextmanager
def capturing() -> Iterator[None]:
    """Mark a client call: library output in this context is routed. Re-entrant."""
    token = _depth.set(_depth.get() + 1)
    try:
        yield
    finally:
        _depth.reset(token)


def is_capturing() -> bool:
    """Whether the current thread / context is inside a client call."""
    return _depth.get() > 0


def in_current_context(fn: Callable[..., T]) -> Callable[..., T]:
    """Wrap `fn` to run in a copy of the caller's context, e.g. in worker threads.

    Each call gets its own copy, so the wrapper can run in several threads at once.
    """
    context = contextvars.copy_context()

    @functools.wraps(fn)
    def run(*args: Any, **kwargs: Any) -> T:
        return context.copy().run(fn, *args, **kwargs)

    return run


def warn(message: str, category: type[Warning], stacklevel: int = 1) -> None:
    """`warnings.warn` for client code, not counting the `capturing()` wrappers.

    `stacklevel` is as for `warnings.warn` called by the caller of `warn`: 2
    reports the warning at that caller's caller (the user's code), even when
    a public method wrapper sits in between. (`warnings.warn`'s own
    `skip_file_prefixes` doesn't skip these frames reliably across Python
    versions, hence the explicit walk.)
    """
    stack: list[FrameType] = []  # stack[0] is this function's frame
    frame: FrameType | None = sys._getframe(0)
    while frame is not None:
        stack.append(frame)
        frame = frame.f_back

    index = 1  # the caller of `warn`
    for _ in range(stacklevel - 1):
        index += 1
        while index < len(stack) and stack[index].f_code.co_filename == _THIS_FILE:
            index += 1
    # `warnings.warn(stacklevel=n)` reports at stack[n - 1], counted from here
    warnings.warn(message, category, stacklevel=min(index, len(stack) - 1) + 1)


def user_stacklevel() -> int:
    """`stacklevel` reaching the first caller outside `mp_api`, for `mp_warning` etc.

    Relative to the function calling `user_stacklevel` (1 is that function),
    not counting the public method wrappers, as `warn` counts.
    """
    level = 1
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_filename != _THIS_FILE:
            if frame.f_globals.get("__name__", "").split(".")[0] != "mp_api":
                return level
            level += 1
        frame = frame.f_back  # type: ignore[assignment]
    return 1


def _tracked(fn: Callable[..., Any]) -> Callable[..., Any]:
    if getattr(fn, "__mp_tracked__", False):
        return fn

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with capturing():
            return fn(*args, **kwargs)

    wrapper.__mp_tracked__ = True  # type: ignore[attr-defined]
    return wrapper


def track_calls(cls: type[T]) -> type[T]:
    """Make the public methods `cls` defines run inside `capturing()`.

    Covers plain functions, static and class methods (not properties or other
    callable attributes), plus `__init__` and `__getitem__`. Inherited methods are wrapped where they're
    defined. Safe to apply more than once. Usable as a class decorator.
    """
    for name, attr in list(vars(cls).items()):
        if name.startswith("_") and name not in _WRAPPED_DUNDERS:
            continue
        if isinstance(attr, staticmethod | classmethod):
            if inspect.isfunction(fn := attr.__func__):
                wrapped = _tracked(fn)
                if wrapped is not fn:
                    setattr(cls, name, type(attr)(wrapped))
        elif inspect.isfunction(attr):
            wrapped = _tracked(attr)
            if wrapped is not attr:
                setattr(cls, name, wrapped)
    return cls


# --------------------------------------------------------------------------
# Re-emitting
# --------------------------------------------------------------------------


def _package_path(filename: str, package: str) -> str:
    """`filename` from the package directory on, e.g. "pymatgen/core/structure.py"."""
    parts = Path(filename).parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == package:
            return "/".join(parts[index:])
    return Path(filename).name


def _emit(
    package: str,
    level: int,
    message: str,
    pathname: str,
    lineno: int,
    func: str | None,
) -> None:
    logger = logging.getLogger(f"{EXTERNAL_LOGGER}.{package}")
    if not logger.isEnabledFor(level):
        return
    origin = f"{_package_path(pathname, package)}:{lineno}"
    record = logger.makeRecord(
        logger.name,
        level,
        pathname,
        lineno,
        f"{message} ({origin})",
        (),
        None,
        func=func,
        extra={"mp_message": message, "mp_origin": origin, "mp_package": package},
    )
    logger.handle(record)


def _location(filename: str, lineno: int) -> str:
    """`filename:lineno`, relative to the working directory if it's below it."""
    path = Path(filename)
    if path.is_absolute():
        try:
            filename = str(path.relative_to(Path.cwd()))
        except (ValueError, OSError):
            pass
    return f"{filename}:{lineno}"


def _render_own(category: type[Warning], message: str, filename: str, lineno: int) -> bool:
    """Show one of the client's warnings on the console, if it's interactive."""
    from mp_api.client.core._display import print_warning

    return print_warning(category.__name__, message, _location(filename, lineno))


def _warning_origin() -> FrameType | None:
    """The frame that called `warnings.warn` (or C code that warned).

    Ignores `stacklevel`: libraries often pass `stacklevel=2` to report a
    warning at their caller, which for a client call is the client's own code.
    """
    frame: FrameType | None = sys._getframe(1)
    while frame is not None and frame.f_globals.get("__name__") in _WARNINGS_MODULES:
        frame = frame.f_back
    return frame


class _WarningHook:
    """Chained `warnings.showwarning`, see module docstring."""

    def __init__(self, previous: Callable[..., None]) -> None:
        self.previous = previous

    def _prints_by_default(self) -> bool:
        """Whether the hook below would print with Python's default printer.

        False if an application put its own hook below ours (e.g.
        `logging.captureWarnings(True)` before importing the client), or if
        warnings are being recorded (`catch_warnings(record=True)`).
        """
        # `catch_warnings(record=True)` swaps the printer for `list.append`
        return self.previous is getattr(
            warnings, "_showwarning_orig", None
        ) and inspect.isfunction(getattr(warnings, "_showwarnmsg_impl", None))

    def __call__(
        self,
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:
        origin = _warning_origin()
        module = origin.f_globals.get("__name__", "") if origin else ""
        if module.split(".")[0] == "mp_api":
            if file is None and self._prints_by_default() and _render_own(
                category, str(message), filename, lineno
            ):
                return
        elif is_capturing() and not issubclass(category, _PASS_THROUGH_CATEGORIES):
            if origin is not None:
                text = str(message)
                if category is not UserWarning:
                    text = f"{category.__name__}: {text}"
                _emit(
                    module.split(".")[0] or "unknown",
                    logging.WARNING,
                    text,
                    origin.f_code.co_filename,
                    origin.f_lineno,
                    origin.f_code.co_name,
                )
                return
        self.previous(message, category, filename, lineno, file, line)


class _LastResortHandler(logging.Handler):
    """Replacement for `logging.lastResort`, see module docstring."""

    def __init__(self, previous: logging.Handler) -> None:
        super().__init__(previous.level)
        self.previous = previous

    def handle(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        package = record.name.split(".")[0]
        if is_capturing() and package != "mp_api":
            _emit(
                package or "root",
                record.levelno,
                record.getMessage(),
                record.pathname,
                record.lineno,
                record.funcName,
            )
            return True
        return bool(self.previous.handle(record))

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - unused
        self.handle(record)


_install_lock = threading.Lock()
_installed = False


def install() -> None:
    """Install the warnings hook and the logging fallback, once per process."""
    global _installed
    with _install_lock:
        if _installed:
            return
        warnings.showwarning = _WarningHook(warnings.showwarning)
        if logging.lastResort is not None:
            logging.lastResort = _LastResortHandler(logging.lastResort)
        _installed = True
