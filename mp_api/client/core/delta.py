"""Manage DeltaTable snapshots and SQL execution for delta-backed routes.

`deltalake.QueryBuilder.register` copies a table's snapshot (its list of
data files) into a DataFusion session at registration time. The snapshot
then can't be updated or deregistered, and registering the same name again
raises.

If the remote table is vacuumed after an update, an old snapshot can point
to data files that no longer exist. The only way to recover is to load the
table again and register it on a new QueryBuilder.

`DeltaCatalog` owns the DeltaTables and the QueryBuilder they are registered
on. When a query fails because an object is missing, it reloads only the
table named in that query, swaps in a new QueryBuilder with every table
registered on it, and retries the query once.

Blocking native calls can be sent to a pluggable runner (e.g. a threadpool),
see `DeltaCatalog`.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from deltalake import DeltaTable, QueryBuilder

if TYPE_CHECKING:
    from collections.abc import Callable

    from arro3.core import RecordBatchReader

    # Takes a zero-argument function, runs it, returns its result
    Runner = Callable[[Callable[[], Any]], Any]

logger = logging.getLogger(__name__)


def _call_directly(fn: Callable[[], Any]) -> Any:
    """Default runner: run `fn` in the calling thread."""
    return fn()


# Messages that mean a data or log file referenced by the current snapshot
# is gone (e.g. removed by a vacuum on the remote table).
# DataFusion errors reach Python as a generic `DeltaError`, so the message
# has to be matched as well as the exception type. Example:
#   "Failed to fetch metadata for file ...: Parquet error: External:
#    Object at location ... not found: No such file or directory (os error 2)"
_MISSING_OBJECT_PATTERN = re.compile(
    r"object at location .* not found"
    r"|notfound"
    r"|not found"
    r"|no such file or directory"
    r"|status code: 404",
    re.IGNORECASE,
)


def _is_missing_object(exc: BaseException) -> bool:
    """Whether an exception means a file in the snapshot no longer exists.

    Args:
        exc (BaseException) : exception raised by deltalake / DataFusion

    Returns:
        bool
    """
    if isinstance(exc, FileNotFoundError):
        return True
    return bool(_MISSING_OBJECT_PATTERN.search(str(exc)))


@dataclass
class _Entry:
    """A DeltaTable registered under a label, plus what's needed to reload it."""

    label: str
    uri: str
    table: DeltaTable
    storage_options: dict[str, str] | None = None
    # Increases each time this table is reloaded. Used to tell whether
    # another thread already refreshed it.
    generation: int = 0


class DeltaCatalog:
    """Thread-safe cache of DeltaTables and the QueryBuilder they are registered on.

    One catalog can be shared by every rester in a process.
    Snapshots stay fixed until a query fails because a
    referenced object is missing, then only that table is reloaded.

    Blocking native work (loading a table's snapshot from storage, and
    running a query) can be sent to a `runner`. A runner is any callable
    that takes a zero-argument function, runs it, and returns its result
    or raises its exception. Under gevent, for example, running native calls
    in a real thread stops them from blocking the event loop:

    ```python
    import gevent

    catalog = DeltaCatalog(runner=gevent.get_hub().threadpool.apply)
    ```

    or, with a standard executor:

    ```python
    from concurrent.futures import ThreadPoolExecutor

    pool = ThreadPoolExecutor(8)
    catalog = DeltaCatalog(runner=lambda fn: pool.submit(fn).result())
    ```

    The catalog's own locking and bookkeeping always run in the calling
    thread / greenlet, never inside the runner. The catalog-wide lock is
    never held during a load or query, so a slow load of one table doesn't
    block queries on other tables.
    """

    def __init__(self, runner: Runner | None = None) -> None:
        """Create an empty catalog.

        Args:
            runner (callable or None) : runs blocking native calls, see the
                class docstring. If None, they run directly in the caller.
        """
        self._runner: Runner = runner or _call_directly
        self._entries: dict[str, _Entry] = {}  # keyed by URI
        self._labels: dict[str, str] = {}  # label -> URI
        self._qb: QueryBuilder = QueryBuilder()
        # Guards _entries, _labels, _qb and _load_locks. Only held for
        # in-memory work, never across a runner call.
        self._lock = threading.RLock()
        # One lock per URI, held while that table is (re)loaded so concurrent
        # loads of the same table collapse into one.
        self._load_locks: dict[str, threading.Lock] = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tables={self.labels})"

    @property
    def runner(self) -> Runner:
        """The callable used to run blocking native calls."""
        return self._runner

    @property
    def labels(self) -> list[str]:
        """Labels (SQL table names) of all registered tables."""
        with self._lock:
            return list(self._labels)

    @property
    def tables(self) -> dict[str, DeltaTable]:
        """Map of label to currently registered DeltaTable."""
        with self._lock:
            return {
                label: self._entries[uri].table for label, uri in self._labels.items()
            }

    def __contains__(self, label: str) -> bool:
        with self._lock:
            return label in self._labels

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def add(
        self,
        label: str,
        table: DeltaTable,
        storage_options: dict[str, str] | None = None,
        uri: str | None = None,
    ) -> tuple[str, DeltaTable]:
        """Register an already-constructed DeltaTable.

        If a table with the same URI is already registered, the stored
        label and table are returned and `table` is discarded.

        Args:
            label (str) : SQL table name
            table (DeltaTable) : the table to register
            storage_options (dict or None) : storage options used to reload
                the table. Defaults to the options the table was created with.
            uri (str or None) : cache key. Defaults to `table.table_uri`.

        Returns:
            tuple of the label the table is registered under and the DeltaTable.

        Raises:
            ValueError: if `label` is already used by a table with a different URI.
        """
        uri = uri or table.table_uri
        with self._lock:
            if (existing := self._entries.get(uri)) is not None:
                return existing.label, existing.table
            self._check_label_free(label, uri)
            self._qb.register(label, table)
            self._entries[uri] = _Entry(
                label=label,
                uri=uri,
                table=table,
                storage_options=(
                    storage_options
                    if storage_options is not None
                    else getattr(table, "_storage_options", None)
                ),
            )
            self._labels[label] = uri
            return label, table

    def get_table(
        self,
        uri: str,
        label: str,
        storage_options: dict[str, str] | None = None,
        refresh: bool = False,
    ) -> tuple[str, DeltaTable]:
        """Get a cached DeltaTable, or load and register it.

        Args:
            uri (str) : table URI, also the cache key
            label (str) : SQL table name to register a new table under
            storage_options (dict or None) : storage options for a newly loaded table
            refresh (bool) : if the table is already cached, reload it first.
                Skipped if another caller reloaded it while this one waited.

        Returns:
            tuple of the label the table is registered under (may differ from
            `label` if the URI was registered earlier under another name) and
            the DeltaTable.

        Raises:
            ValueError: if `label` is already used by a table with a different URI.
        """
        with self._lock:
            entry = self._entries.get(uri)
            if entry is not None and not refresh:
                return entry.label, entry.table
            if entry is None:
                # fail fast, before any network I/O
                self._check_label_free(label, uri)
            seen_generation = entry.generation if entry is not None else None
            load_lock = self._load_lock(uri)

        with load_lock:
            with self._lock:
                entry = self._entries.get(uri)

            if entry is None:
                table = self._load(uri, storage_options)
                return self.add(label, table, storage_options=storage_options, uri=uri)

            # Reload only if nobody else loaded / reloaded it while we waited
            if seen_generation is not None and entry.generation == seen_generation:
                self._reload(entry)
            return entry.label, entry.table

    def execute(self, sql: str, label: str | None = None) -> pa.Table:
        """Run a SQL query and return the full result.

        If `label` is given and the query fails because an object is missing,
        that table is reloaded and the query is retried once. Without
        `label`, errors are raised as-is.

        Args:
            sql (str) : SQL query
            label (str or None) : the table the query reads from

        Returns:
            pyarrow.Table

        Raises:
            Whatever deltalake / DataFusion / pyarrow raises. If the retry
            also fails, its exception has a note saying the table was refreshed.
        """
        with self._lock:
            qb = self._qb
            entry = self._entries.get(self._labels.get(label, "")) if label else None
            seen_generation = entry.generation if entry else None

        try:
            return self._runner(partial(self._run, qb, sql))
        except Exception as exc:
            if entry is None or not _is_missing_object(exc):
                raise
            logger.warning(
                f"Query on DeltaTable '{label}' referenced a missing object, "
                f"refreshing snapshot and retrying: {exc}"
            )

        qb = self._refresh(entry, seen_generation)  # type: ignore[arg-type]
        try:
            return self._runner(partial(self._run, qb, sql))
        except Exception as exc:
            exc.add_note(
                f"Query failed again after refreshing DeltaTable '{label}' ({entry.uri})."
            )
            raise

    def execute_stream(self, sql: str) -> RecordBatchReader:
        """Run a SQL query and stream the results, without retrying.

        Used for full-dataset downloads, where batches may already have been
        written to disk before an error, so a transparent retry isn't safe.
        Call `get_table(..., refresh=True)` first to start from the latest snapshot.

        Does not use the runner: batches are fetched lazily as the returned
        reader is consumed, in the consuming thread.

        Args:
            sql (str) : SQL query

        Returns:
            arro3 RecordBatchReader
        """
        with self._lock:
            qb = self._qb
        return qb.execute(sql)

    @staticmethod
    def _run(qb: QueryBuilder, sql: str) -> pa.Table:
        # Read via pyarrow's C stream interface rather than arro3's
        # `read_all()`: arro3 holds the GIL while it fetches every batch,
        # pyarrow releases it, so other threads (and, with a threadpool
        # runner, the gevent loop) keep running during the fetch.
        # A missing-file error can surface while planning (execute) or while
        # reading batches; both happen inside the caller's try.
        return pa.table(qb.execute(sql))

    def _load(self, uri: str, storage_options: dict[str, str] | None) -> DeltaTable:
        """Load a table snapshot from storage via the runner. Caller holds the URI's load lock."""
        return self._runner(partial(DeltaTable, uri, storage_options=storage_options))

    def _load_lock(self, uri: str) -> threading.Lock:
        """Get or create the load lock for a URI. Caller holds the catalog lock."""
        if (lock := self._load_locks.get(uri)) is None:
            lock = self._load_locks[uri] = threading.Lock()
        return lock

    def _check_label_free(self, label: str, uri: str) -> None:
        if (other := self._labels.get(label)) is not None and other != uri:
            raise ValueError(
                f"Label '{label}' is already registered for DeltaTable {other}, "
                f"cannot register it for {uri}."
            )

    def _refresh(self, entry: _Entry, seen_generation: int) -> QueryBuilder:
        """Reload `entry` unless another caller already did, and return the current QueryBuilder."""
        with self._lock:
            load_lock = self._load_lock(entry.uri)
        with load_lock:
            if entry.generation == seen_generation:
                self._reload(entry)
        with self._lock:
            return self._qb

    def _reload(self, entry: _Entry) -> None:
        """Reload one table's snapshot and swap in a new QueryBuilder.

        Caller holds the entry's load lock, but not the catalog lock: the
        load runs without it, then the catalog lock is taken briefly to swap.

        Builds a new DeltaTable instead of calling `update_incremental()`, in
        case the table was rebuilt rather than appended to. Other tables keep
        their snapshots; registering them again only copies in-memory state.
        Queries already running keep using the old QueryBuilder.
        """
        table = self._load(entry.uri, entry.storage_options)

        with self._lock:
            # Rebuild from the entries as they are now, so a concurrent
            # reload of a different table isn't lost.
            qb = QueryBuilder()
            for other in self._entries.values():
                qb.register(other.label, table if other is entry else other.table)
            entry.table = table
            entry.generation += 1
            self._qb = qb

        logger.info(
            f"Refreshed DeltaTable '{entry.label}' ({entry.uri}) "
            f"to version {table.version()}."
        )
