"""Tests for DeltaCatalog snapshot caching and refresh-on-missing-object retry.

deltalake's DeltaTable and QueryBuilder are replaced with in-memory fakes, so
these tests need no network access, API key, or files on disk.
"""

import threading
import warnings

import pyarrow as pa
import pytest
from deltalake.exceptions import DeltaError

import mp_api.client.core.delta as delta_mod
from mp_api.client.core.client import BaseRester, QueryBuilderWithCache, _Rester
from mp_api.client.core.delta import DeltaCatalog, _is_missing_object
from mp_api.client.core.exceptions import MPRestError, MPRestWarning

REAL_ERROR = (
    "Failed to fetch metadata for file Users/tsmathis/mp_datasets/build/collections/"
    "materials/version=2026-04-13/group-4-part-0.zstd.parquet: Parquet error: External: "
    "Object at location /Users/tsmathis/mp_datasets/build/collections/materials/"
    "version=2026-04-13/group-4-part-0.zstd.parquet not found: No such file or "
    "directory (os error 2)"
)


class FakeDeltaTable:
    """Stand-in for deltalake.DeltaTable; each construction is a new 'snapshot'."""

    loads: list[str] = []

    def __init__(self, uri, storage_options=None, **kwargs):
        self.table_uri = uri
        self._storage_options = storage_options
        FakeDeltaTable.loads.append(uri)
        self.snapshot = FakeDeltaTable.loads.count(uri)

    def version(self):
        return self.snapshot


class FakeReader:
    """Arrow C-stream producer, like the arro3 reader returned by QueryBuilder.execute."""

    def __init__(self, result):
        self._result = result

    def __arrow_c_stream__(self, requested_schema=None):
        if isinstance(self._result, Exception):
            # error surfacing while batches are read
            raise self._result
        return self._result.__arrow_c_stream__(requested_schema)


class FakeQueryBuilder:
    """Stand-in for deltalake.QueryBuilder that can be told to fail."""

    instances: list["FakeQueryBuilder"] = []
    # Queue of exceptions raised by successive execute() calls (any builder)
    failures: list[Exception] = []
    # Raise failures while reading batches instead of from execute()
    fail_on_read: bool = False

    def __init__(self):
        self.registered: dict[str, FakeDeltaTable] = {}
        FakeQueryBuilder.instances.append(self)

    def register(self, table_name, delta_table):
        if table_name in self.registered:
            raise DeltaError(f"The table {table_name} already exists")
        self.registered[table_name] = delta_table
        return self

    def execute(self, sql):
        result = pa.table({"sql": [sql]})
        if FakeQueryBuilder.failures:
            exc = FakeQueryBuilder.failures.pop(0)
            if not FakeQueryBuilder.fail_on_read:
                raise exc
            result = exc
        return FakeReader(result)


@pytest.fixture(autouse=True)
def fake_deltalake(monkeypatch):
    FakeDeltaTable.loads = []
    FakeQueryBuilder.instances = []
    FakeQueryBuilder.failures = []
    FakeQueryBuilder.fail_on_read = False
    monkeypatch.setattr(delta_mod, "DeltaTable", FakeDeltaTable)
    monkeypatch.setattr(delta_mod, "QueryBuilder", FakeQueryBuilder)
    # QueryBuilderWithCache subclasses the real QueryBuilder; skip its native init
    monkeypatch.setattr(
        "deltalake.query.QueryBuilder.__init__", lambda self: None, raising=True
    )


@pytest.fixture
def catalog():
    cat = DeltaCatalog()
    cat.get_table("s3a://bucket/a/", "a")
    cat.get_table("s3a://bucket/b/", "b")
    return cat


# --- _is_missing_object --------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        DeltaError(REAL_ERROR),
        OSError(REAL_ERROR),
        FileNotFoundError("gone"),
        DeltaError("Generic S3 error: ... status code: 404 Not Found"),
        DeltaError("Object Store error: NotFound { path: ... }"),
    ],
)
def test_is_missing_object_matches(exc):
    assert _is_missing_object(exc)


@pytest.mark.parametrize(
    "exc",
    [
        DeltaError('SQL error: ParserError("Expected: an expression")'),
        DeltaError("Schema error: No field named foo"),
        OSError("Generic S3 error: request timed out"),
    ],
)
def test_is_missing_object_ignores_other_errors(exc):
    assert not _is_missing_object(exc)


# --- caching -------------------------------------------------------------------


def test_get_table_caches_by_uri(catalog):
    label, table = catalog.get_table("s3a://bucket/a/", "a")
    assert label == "a"
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 1
    assert catalog.labels == ["a", "b"]
    assert "a" in catalog and len(catalog) == 2
    assert catalog.tables["a"] is table


def test_get_table_returns_stored_label_for_known_uri(catalog):
    label, _ = catalog.get_table("s3a://bucket/a/", "other_name")
    assert label == "a"
    assert "other_name" not in catalog


def test_label_collision_with_different_uri_raises(catalog):
    with pytest.raises(ValueError, match="already registered"):
        catalog.get_table("s3a://bucket/c/", "a")


def test_get_table_refresh_reloads_only_that_table(catalog):
    _, old_b = catalog.get_table("s3a://bucket/b/", "b")
    old_qb = catalog._qb

    _, new_a = catalog.get_table("s3a://bucket/a/", "a", refresh=True)

    assert new_a.snapshot == 2
    assert catalog._qb is not old_qb
    # new builder has every table, with untouched tables carried over as-is
    assert catalog._qb.registered == {"a": new_a, "b": old_b}
    assert FakeDeltaTable.loads.count("s3a://bucket/b/") == 1


# --- execute / retry -----------------------------------------------------------


def test_execute_success_no_refresh(catalog):
    result = catalog.execute("SELECT * FROM a", label="a")
    assert result["sql"].to_pylist() == ["SELECT * FROM a"]
    assert len(FakeQueryBuilder.instances) == 1


@pytest.mark.parametrize("fail_on_read", [False, True])
def test_missing_object_refreshes_named_table_and_retries(catalog, fail_on_read):
    FakeQueryBuilder.fail_on_read = fail_on_read
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
    _, old_b = catalog.get_table("s3a://bucket/b/", "b")

    result = catalog.execute("SELECT * FROM a", label="a")

    assert result.num_rows == 1
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 2
    assert FakeDeltaTable.loads.count("s3a://bucket/b/") == 1
    assert catalog.tables["b"] is old_b
    assert catalog.tables["a"].snapshot == 2
    assert set(catalog._qb.registered) == {"a", "b"}


def test_non_missing_error_is_not_retried(catalog):
    FakeQueryBuilder.failures = [DeltaError("SQL error: bad syntax")]
    with pytest.raises(DeltaError, match="bad syntax"):
        catalog.execute("SELECT * FROM a", label="a")
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 1


def test_no_label_is_not_retried(catalog):
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
    with pytest.raises(DeltaError):
        catalog.execute("SELECT * FROM a")
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 1


def test_second_failure_raises_with_note(catalog):
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR), DeltaError(REAL_ERROR)]
    with pytest.raises(DeltaError) as excinfo:
        catalog.execute("SELECT * FROM a", label="a")
    assert any("after refreshing" in n for n in excinfo.value.__notes__)
    # exactly one refresh
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 2


def test_concurrent_refresh_is_not_repeated(catalog):
    """A refresh by another thread between failure and retry isn't redone."""
    entry = catalog._entries["s3a://bucket/a/"]
    seen = entry.generation
    catalog.get_table("s3a://bucket/a/", "a", refresh=True)  # "other thread"
    loads_before = len(FakeDeltaTable.loads)

    qb = catalog._refresh(entry, seen)

    assert len(FakeDeltaTable.loads) == loads_before
    assert qb is catalog._qb


# --- runner hook ---------------------------------------------------------------


class RecordingRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, fn):
        name = getattr(getattr(fn, "func", fn), "__name__", repr(fn))
        self.calls.append(name)
        return fn()


def test_default_runner_calls_directly():
    cat = DeltaCatalog()
    assert cat.runner(lambda: 42) == 42


def test_runner_wraps_loads_queries_and_reloads():
    runner = RecordingRunner()
    cat = DeltaCatalog(runner=runner)

    cat.get_table("s3a://bucket/a/", "a")
    assert runner.calls == ["FakeDeltaTable"]

    cat.execute("SELECT * FROM a", label="a")
    assert runner.calls[-1] == "_run"

    runner.calls.clear()
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
    assert cat.execute("SELECT * FROM a", label="a").num_rows == 1
    # failed query, reload, retried query
    assert runner.calls == ["_run", "FakeDeltaTable", "_run"]

    runner.calls.clear()
    cat.get_table("s3a://bucket/a/", "a", refresh=True)
    assert runner.calls == ["FakeDeltaTable"]

    # cache hit: no native work
    runner.calls.clear()
    cat.get_table("s3a://bucket/a/", "a")
    assert runner.calls == []


def test_runner_exceptions_propagate():
    def runner(fn):
        return fn()

    cat = DeltaCatalog(runner=runner)
    cat.get_table("s3a://bucket/a/", "a")
    FakeQueryBuilder.failures = [DeltaError("SQL error: bad syntax")]
    with pytest.raises(DeltaError, match="bad syntax"):
        cat.execute("SELECT * FROM a", label="a")


def test_threadpool_runner():
    from concurrent.futures import ThreadPoolExecutor

    main = threading.get_ident()
    seen = []

    with ThreadPoolExecutor(2) as pool:

        def runner(fn):
            def wrapped():
                seen.append(threading.get_ident())
                return fn()

            return pool.submit(wrapped).result()

        cat = DeltaCatalog(runner=runner)
        cat.get_table("s3a://bucket/a/", "a")
        FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
        assert cat.execute("SELECT * FROM a", label="a").num_rows == 1

    assert seen and main not in seen


# --- concurrency ---------------------------------------------------------------


class BlockingLoads:
    """Patch FakeDeltaTable so loads of one URI block until released."""

    def __init__(self, monkeypatch, uri):
        self.uri = uri
        self.started = threading.Event()
        self.release = threading.Event()
        original = FakeDeltaTable.__init__

        def init(table, table_uri, storage_options=None, **kwargs):
            if table_uri == self.uri:
                self.started.set()
                assert self.release.wait(5), "test timed out waiting for release"
            original(table, table_uri, storage_options=storage_options, **kwargs)

        monkeypatch.setattr(FakeDeltaTable, "__init__", init)


def _in_thread(fn, *args, **kwargs):
    result = {}

    def target():
        try:
            result["value"] = fn(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - surfaced via assert
            result["error"] = exc

    th = threading.Thread(target=target, daemon=True)
    th.start()
    return th, result


def test_reload_does_not_block_queries_on_other_tables(catalog, monkeypatch):
    blocker = BlockingLoads(monkeypatch, "s3a://bucket/a/")

    th, res = _in_thread(catalog.get_table, "s3a://bucket/a/", "a", refresh=True)
    assert blocker.started.wait(5)

    # While a's reload is stuck in the network call, b is still queryable
    # and a new table can be added.
    assert catalog.execute("SELECT * FROM b", label="b").num_rows == 1
    catalog.get_table("s3a://bucket/c/", "c")

    blocker.release.set()
    th.join(5)
    assert "error" not in res
    # reload swapped in a builder holding all three tables
    assert set(catalog._qb.registered) == {"a", "b", "c"}
    assert catalog.tables["a"].snapshot == 2


def test_concurrent_first_loads_of_same_uri_load_once(monkeypatch):
    cat = DeltaCatalog()
    blocker = BlockingLoads(monkeypatch, "s3a://bucket/a/")

    t1, r1 = _in_thread(cat.get_table, "s3a://bucket/a/", "a")
    assert blocker.started.wait(5)
    t2, r2 = _in_thread(cat.get_table, "s3a://bucket/a/", "a")

    blocker.release.set()
    t1.join(5)
    t2.join(5)

    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 1
    assert r1["value"][1] is r2["value"][1]


def test_concurrent_refreshes_of_same_table_reload_once(catalog, monkeypatch):
    blocker = BlockingLoads(monkeypatch, "s3a://bucket/a/")
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR), DeltaError(REAL_ERROR)]

    t1, r1 = _in_thread(catalog.execute, "SELECT * FROM a", label="a")
    assert blocker.started.wait(5)
    t2, r2 = _in_thread(catalog.execute, "SELECT * FROM a", label="a")

    blocker.release.set()
    t1.join(5)
    t2.join(5)

    assert "error" not in r1 and "error" not in r2
    # initial load + exactly one reload
    assert FakeDeltaTable.loads.count("s3a://bucket/a/") == 2


def test_failed_load_is_not_registered(monkeypatch):
    cat = DeltaCatalog()

    def boom(table, table_uri, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(FakeDeltaTable, "__init__", boom)
    with pytest.raises(OSError):
        cat.get_table("s3a://bucket/a/", "a")
    assert "a" not in cat and len(cat) == 0


def test_failed_reload_keeps_old_snapshot(catalog, monkeypatch):
    old_a = catalog.tables["a"]
    old_qb = catalog._qb

    def boom(table, table_uri, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(FakeDeltaTable, "__init__", boom)
    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
    with pytest.raises(OSError):
        catalog.execute("SELECT * FROM a", label="a")
    assert catalog.tables["a"] is old_a
    assert catalog._qb is old_qb


# --- rester integration --------------------------------------------------------


@pytest.fixture
def no_heartbeat(monkeypatch):
    monkeypatch.setattr(
        BaseRester, "_get_heartbeat_info", staticmethod(lambda endpoint: ("v", []))
    )


def test_rester_creates_catalog_lazily():
    rester = _Rester(api_key="a" * 32)
    assert rester._delta_catalog is None
    assert isinstance(rester.delta_catalog, DeltaCatalog)
    assert rester.delta_catalog is rester.delta_catalog


def test_rester_uses_provided_catalog():
    cat = DeltaCatalog()
    assert _Rester(api_key="a" * 32, delta_catalog=cat).delta_catalog is cat


def test_query_builder_with_cache_is_deprecated_but_shared():
    with pytest.warns(DeprecationWarning, match="QueryBuilderWithCache"):
        qb = QueryBuilderWithCache()
    r1 = _Rester(api_key="a" * 32, query_builder=qb)
    r2 = _Rester(api_key="a" * 32, query_builder=qb)
    assert r1.delta_catalog is r2.delta_catalog is qb.catalog


def test_query_builder_with_cache_register_and_introspect():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        qb = QueryBuilderWithCache()
    table = FakeDeltaTable("s3a://bucket/x/")
    assert qb.register("x", table) is qb
    assert qb._delta_tables == {"x": table}
    assert "x" in qb.catalog


def test_query_builder_property_is_deprecated():
    rester = _Rester(api_key="a" * 32)
    with pytest.warns(DeprecationWarning, match="delta_catalog"):
        qb = rester.query_builder
    assert qb.catalog is rester.delta_catalog


def test_sub_resters_share_parent_catalog(no_heartbeat):
    from mp_api.client.routes.materials.materials import MaterialsRester

    cat = DeltaCatalog()
    materials = MaterialsRester(api_key="a" * 32, delta_catalog=cat)
    assert materials.thermo.delta_catalog is cat
    assert materials.tasks.delta_catalog is cat
    assert materials.phonon.summary_rester.delta_catalog is cat


def test_get_delta_table_warns_on_label_mismatch(no_heartbeat):
    rester = BaseRester(api_key="a" * 32)
    lbl, _ = rester._get_delta_table("bucket", "some/prefix", label="first")
    assert lbl == "first"
    assert rester.delta_catalog.tables["first"].table_uri == "s3a://bucket/some/prefix/"
    with pytest.warns(MPRestWarning, match="different label"):
        lbl, _ = rester._get_delta_table("bucket", "some/prefix/", label="second")
    assert lbl == "first"


def test_query_delta_single_retries_and_wraps_errors(no_heartbeat):
    rester = BaseRester(api_key="a" * 32)
    lbl, _ = rester._get_delta_table("bucket", "prefix", label="tbl")

    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR)]
    assert rester._query_delta_single("SELECT 1", label=lbl).num_rows == 1

    FakeQueryBuilder.failures = [DeltaError(REAL_ERROR), DeltaError(REAL_ERROR)]
    with pytest.raises(MPRestError, match="refreshed and the query retried"):
        rester._query_delta_single("SELECT 1", label=lbl)

    FakeQueryBuilder.failures = [DeltaError("request timed out")]
    with pytest.raises(MPRestError, match="increasing the 'timeout'"):
        rester._query_delta_single("SELECT 1", label=lbl)


def test_execute_stream_returns_pyarrow_reader(catalog):
    """Streaming must go through pyarrow, which releases the GIL between batches
    (arro3 iteration holds it, freezing e.g. the progress bar refresh thread)."""
    reader = catalog.execute_stream("SELECT * FROM a")
    assert isinstance(reader, pa.RecordBatchReader)
    batches = list(reader)
    assert sum(b.num_rows for b in batches) == 1
    assert all(isinstance(b, pa.RecordBatch) for b in batches)
