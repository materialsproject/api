"""Full downloads of DeltaTables partitioned by database version, without network access.

The "remote" tables are local DeltaTables; `_get_delta_table` is pointed at
them through the rester's DeltaCatalog.
"""

import inspect
import io
import logging
import os
import re

import pyarrow as pa
import pytest
from deltalake import DeltaTable, write_deltalake
from pydantic import BaseModel
from rich.console import Console

import mp_api.client.core._display as display
import mp_api.client.core.client as client_module
from mp_api.client.core.client import BaseRester
from mp_api.client.core.delta import DeltaCatalog
from mp_api.client.core.exceptions import MPRestError
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
from mp_api.client.core.utils import MPDataset, to_db_version, to_partition_version


class BuilderMeta(BaseModel):
    license: str


class Doc(BaseModel):
    material_id: str
    nsites: int
    builder_meta: BuilderMeta


def remote_rows(version: str, n: int, n_nc: int = 0) -> pa.Table:
    """`n` documents for `version`, the last `n_nc` of them BY-NC licensed."""
    return pa.table(
        {
            "material_id": [f"mp-{version}-{i}" for i in range(n)],
            "nsites": list(range(n)),
            "builder_meta": [
                {"license": "BY-NC" if i >= n - n_nc else "BY-4.0"} for i in range(n)
            ],
            "version": [version] * n,
        }
    )


@pytest.fixture
def remote(tmp_path):
    """A remote table with two versions: 10 rows (2 BY-NC), then 6 rows (1 BY-NC)."""
    uri = str(tmp_path / "remote" / "chemenv")
    write_deltalake(uri, remote_rows("2026-04-13", 10, 2), partition_by=["version"])
    write_deltalake(
        uri, remote_rows("2026-09-28", 6, 1), partition_by=["version"], mode="append"
    )
    return uri


class Rester(BaseRester):
    suffix = "materials/chemenv"
    document_model = Doc


@pytest.fixture
def make_rester(tmp_path, remote, monkeypatch):
    monkeypatch.setattr(
        BaseRester,
        "_get_heartbeat_info",
        staticmethod(lambda endpoint: ("2026.09.28", ["gnome_r2scan_statics"])),
    )
    catalog = DeltaCatalog()
    calls = {"gnome": 0, "get_table": []}

    def get_delta_table(
        self, bucket, prefix, connector="s3a", label=None, refresh=False
    ):
        calls["get_table"].append(prefix)
        return catalog.get_table(remote, label or "chemenv", refresh=refresh)

    monkeypatch.setattr(BaseRester, "_get_delta_table", get_delta_table)

    def make(db_version=None, gnome=True, force_renew=False):
        def submit(self, **kwargs):
            calls["gnome"] += 1
            return {"meta": {"total_doc": 1 if gnome else 0}}

        monkeypatch.setattr(BaseRester, "_submit_requests", submit)
        r = Rester(
            api_key="a" * 32,
            db_version=db_version,
            local_dataset_cache=tmp_path / "cache",
            force_renew=force_renew,
            mute_progress_bars=True,
            delta_catalog=catalog,
        )
        r.calls = calls
        return r

    return make


def download(rester) -> MPDataset:
    return rester._query_resource(criteria={})["data"]


def local_path(tmp_path) -> str:
    return str(tmp_path / "cache" / "build" / "collections" / "chemenv")


def ids(dataset: MPDataset) -> set[str]:
    return set(dataset.pyarrow_dataset.to_table()["material_id"].to_pylist())


# --------------------------------------------------------------------------
# Version strings
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "given, partition",
    [
        ("2026.04.13", "2026-04-13"),
        ("2026-04-13", "2026-04-13"),
        ("2026_04_13", "2026-04-13"),
        ("v2026.04.13", "2026-04-13"),
        ("2026.04.13.post1", "2026-04-13-post1"),
    ],
)
def test_version_conversion(given, partition):
    assert to_partition_version(given) == partition
    assert to_db_version(partition) == partition.replace("-", ".")


def test_pinned_version_is_normalized(make_rester):
    assert make_rester(db_version="2026-04-13").db_version == "2026.04.13"
    assert make_rester().db_version == "2026.09.28"  # from the heartbeat


# --------------------------------------------------------------------------
# Listing versions
# --------------------------------------------------------------------------


def test_available_db_versions(make_rester):
    assert make_rester().available_db_versions() == ["2026.04.13", "2026.09.28"]


def point_at(monkeypatch, uri, label="flat"):
    """Make `_get_delta_table` load `uri` on the rester's own catalog."""
    monkeypatch.setattr(
        BaseRester,
        "_get_delta_table",
        lambda self, *a, label=None, refresh=False, **k: self.delta_catalog.get_table(
            uri, "flat", refresh=refresh
        ),
    )


def test_available_db_versions_unversioned(make_rester, tmp_path, monkeypatch):
    uri = str(tmp_path / "flat")
    write_deltalake(uri, pa.table({"x": [1]}))
    point_at(monkeypatch, uri)
    with pytest.raises(MPRestError, match="not partitioned by database version"):
        make_rester().available_db_versions()


def test_available_db_versions_not_delta_backed(make_rester):
    r = make_rester()
    r.delta_backed = False
    with pytest.raises(MPRestError, match="not backed by a DeltaTable"):
        r.available_db_versions()


def test_partition_row_counts(remote):
    catalog = DeltaCatalog()
    catalog.get_table(remote, "t")
    assert catalog.partition_row_counts("t") == {"2026-04-13": 10, "2026-09-28": 6}
    assert catalog.partition_row_counts("t", column="nope") is None


# --------------------------------------------------------------------------
# Downloads
# --------------------------------------------------------------------------


def test_downloads_only_the_current_version(make_rester, tmp_path):
    data = download(make_rester())

    assert data.version == "2026.09.28"
    assert len(data) == 6
    assert ids(data) == {f"mp-2026-09-28-{i}" for i in range(6)}
    assert "version" not in data.pyarrow_dataset.schema.names
    local = DeltaTable(local_path(tmp_path))
    assert local.metadata().partition_columns == ["version"]
    assert [p["version"] for p in local.partitions()] == ["2026-09-28"]


def test_pinned_older_version(make_rester):
    data = download(make_rester(db_version="2026.04.13"))
    assert data.version == "2026.04.13" and len(data) == 10


def test_second_version_is_added_as_a_partition(make_rester, tmp_path):
    download(make_rester())
    data = download(make_rester(db_version="2026.04.13"))

    assert len(data) == 10
    local = DeltaTable(local_path(tmp_path))
    assert sorted(p["version"] for p in local.partitions()) == [
        "2026-04-13",
        "2026-09-28",
    ]
    # each version reads only its own rows
    assert len(MPDataset(local_path(tmp_path), Doc, False, version="2026.09.28")) == 6
    assert len(MPDataset(local_path(tmp_path), Doc, False)) == 16


def test_existing_version_is_returned_without_downloading(make_rester, caplog):
    download(make_rester())
    r = make_rester()
    with caplog.at_level(logging.WARNING, logger="mp_api.client.core.client"):
        data = download(r)

    assert len(data) == 6
    assert "already exists" in caplog.text
    assert r.calls["gnome"] == 1  # only the first download asked the API


def test_force_renew_replaces_only_that_version(make_rester, tmp_path):
    download(make_rester(db_version="2026.04.13"))
    download(make_rester())
    path = local_path(tmp_path)
    old_files = set(os.listdir(os.path.join(path, "version=2026-09-28")))

    data = download(make_rester(force_renew=True))

    assert len(data) == 6
    new_files = set(os.listdir(os.path.join(path, "version=2026-09-28")))
    assert new_files and not (new_files & old_files)  # replaced files are vacuumed
    assert len(MPDataset(path, Doc, False, version="2026.04.13")) == 10


def test_missing_version_lists_available(make_rester):
    with pytest.raises(MPRestError) as exc:
        download(make_rester(db_version="2030.01.01"))
    assert "2030.01.01 is not available" in str(exc.value)
    assert "2026.04.13, 2026.09.28" in str(exc.value)


def test_access_controlled_rows_are_filtered(make_rester):
    assert len(download(make_rester(gnome=False))) == 5  # 6 minus 1 BY-NC


def one_row_batches(reader: pa.RecordBatchReader) -> pa.RecordBatchReader:
    table = reader.read_all()
    return pa.RecordBatchReader.from_batches(
        table.schema, table.to_batches(max_chunksize=1)
    )


def test_multiple_flushes_are_one_commit(make_rester, tmp_path, monkeypatch):
    monkeypatch.setattr(MAPI_CLIENT_SETTINGS, "DATASET_FLUSH_THRESHOLD", 1)
    r = make_rester(db_version="2026.04.13")
    stream = r.delta_catalog.execute_stream

    def small_batches(sql):  # one row per batch, so each flushes separately
        return one_row_batches(stream(sql))

    monkeypatch.setattr(r.delta_catalog, "execute_stream", small_batches)
    data = download(r)

    assert len(data) == 10
    assert len(data.pyarrow_dataset.files) == 10
    local = DeltaTable(local_path(tmp_path))
    assert local.version() == 0  # created in a single commit


def test_interrupted_download_leaves_table_unchanged(
    make_rester, tmp_path, monkeypatch
):
    download(make_rester())
    path = local_path(tmp_path)
    before = DeltaTable(path).version()
    files_before = sorted(
        os.path.relpath(os.path.join(d, f), path)
        for d, _, fs in os.walk(path)
        for f in fs
        if "_delta_log" not in d
    )

    monkeypatch.setattr(MAPI_CLIENT_SETTINGS, "DATASET_FLUSH_THRESHOLD", 1)
    r = make_rester(db_version="2026.04.13")
    stream = r.delta_catalog.execute_stream

    def failing(sql):  # fails after the first batch has been flushed
        reader = one_row_batches(stream(sql))

        def batches():
            for i, batch in enumerate(reader):
                if i == 2:
                    raise KeyboardInterrupt
                yield batch

        return pa.RecordBatchReader.from_batches(reader.schema, batches())

    monkeypatch.setattr(r.delta_catalog, "execute_stream", failing)
    flushed = []
    write = client_module.ds.write_dataset
    monkeypatch.setattr(
        client_module.ds,
        "write_dataset",
        lambda *a, **k: flushed.append(1) or write(*a, **k),
    )
    with pytest.raises(KeyboardInterrupt):
        download(r)
    assert flushed  # files were written before the interruption

    assert DeltaTable(path).version() == before
    files_after = sorted(
        os.path.relpath(os.path.join(d, f), path)
        for d, _, fs in os.walk(path)
        for f in fs
        if "_delta_log" not in d
    )
    assert files_after == files_before  # written-but-uncommitted files removed


def test_legacy_unpartitioned_local_table(make_rester, tmp_path):
    path = local_path(tmp_path)
    write_deltalake(path, pa.table({"material_id": ["old"]}))

    with pytest.raises(MPRestError, match="not partitioned by database version"):
        download(make_rester())

    data = download(make_rester(force_renew=True))
    assert len(data) == 6 and data.version == "2026.09.28"


def test_legacy_non_delta_local_dir(make_rester, tmp_path):
    path = local_path(tmp_path)
    os.makedirs(path)
    pa.parquet.write_table(pa.table({"x": [1]}), os.path.join(path, "a.parquet"))

    with pytest.raises(MPRestError, match="is not a DeltaTable"):
        download(make_rester())


def test_unversioned_remote_table(make_rester, tmp_path, monkeypatch):
    uri = str(tmp_path / "flat")
    rows = remote_rows("x", 4).drop_columns(["version"])
    write_deltalake(uri, rows)
    point_at(monkeypatch, uri)
    data = download(make_rester())
    assert len(data) == 4 and data.version is None
    assert DeltaTable(local_path(tmp_path)).metadata().partition_columns == []

    # force_renew replaces the whole (unversioned) table
    write_deltalake(
        uri, remote_rows("x", 7).drop_columns(["version"]), mode="overwrite"
    )
    assert len(download(make_rester(force_renew=True))) == 7


# --------------------------------------------------------------------------
# MPDataset
# --------------------------------------------------------------------------


def test_mpdataset_skips_files_not_in_the_log(make_rester, tmp_path):
    download(make_rester())
    path = local_path(tmp_path)
    stray = os.path.join(path, "version=2026-09-28", "stray.parquet")
    pa.parquet.write_table(
        remote_rows("2026-09-28", 3).drop_columns(["version"]), stray
    )

    assert len(MPDataset(path, Doc, False, version="2026.09.28")) == 6


def test_mpdataset_version_with_no_rows(make_rester, tmp_path):
    download(make_rester())
    data = MPDataset(local_path(tmp_path), Doc, False, version="2001.01.01")
    assert len(data) == 0
    assert "material_id" in data.pyarrow_dataset.schema.names


# --------------------------------------------------------------------------
# Counting status line
# --------------------------------------------------------------------------


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


@pytest.fixture
def term():
    buf = io.StringIO()
    display.set_console(
        Console(file=buf, force_terminal=True, force_jupyter=False, width=160)
    )
    yield buf
    display.set_console(None)


def test_count_shows_status_then_removes_it(make_rester, term, monkeypatch):
    r = make_rester(gnome=False)
    r.mute_progress_bars = False
    execute = r.delta_catalog.execute
    seen = {}

    def spy(sql, label=None):
        if "COUNT(*)" in sql:
            tasks = display._STATE.progress.tasks
            seen["status"] = [t.description for t in tasks if t.fields.get("status")]
        return execute(sql, label=label)

    monkeypatch.setattr(r.delta_catalog, "execute", spy)
    data = download(r)

    assert len(data) == 5
    assert seen["status"] and "Counting chemenv (v2026.09.28)" in seen["status"][0]
    assert display._STATE.progress is None  # status and bar both gone
    assert "✓ Downloaded 5 Doc documents (v2026.09.28)" in plain(term.getvalue())


def test_count_silent_when_muted(make_rester, caplog):
    r = make_rester(gnome=False)  # muted progress bars: no status, no log line
    with caplog.at_level(logging.DEBUG, logger="mp_api.client"):
        download(r)
    assert not any("Counting chemenv" in rec.message for rec in caplog.records)


def test_count_logged_once_at_info_without_live_display(make_rester, caplog):
    r = make_rester(gnome=False)
    r.mute_progress_bars = False  # enabled, but the test console isn't a terminal
    with caplog.at_level(logging.INFO, logger="mp_api.client"):
        download(r)
    # (caplog may see a record twice: pytest's handler is on both the root
    # and, via the default handler's forwarding, mp_api.client)
    records = {
        id(rec): rec for rec in caplog.records if "Counting chemenv" in rec.message
    }
    assert len(records) == 1
    assert next(iter(records.values())).levelno == logging.INFO


def test_warning_level_app_sees_no_progress_notes(make_rester, monkeypatch):
    """A WARNING-level application (e.g. a web server, no terminal) with progress
    bars enabled gets real warnings only, not progress notes like 'Counting...'."""
    records: list[logging.LogRecord] = []

    class Recorder(logging.Handler):
        def emit(self, record):
            records.append(record)

    root = logging.getLogger()
    handler = Recorder()
    monkeypatch.setattr(root, "handlers", [handler])
    monkeypatch.setattr(root, "level", logging.WARNING)

    r = make_rester(gnome=False)
    r.mute_progress_bars = False
    download(r)
    logging.getLogger("mp_api.client.core.client").warning("a real problem")

    messages = [rec.getMessage() for rec in records]
    assert messages == ["a real problem"]


def test_no_count_query_with_full_access(make_rester, monkeypatch):
    r = make_rester(gnome=True)
    execute = r.delta_catalog.execute
    queries = []
    monkeypatch.setattr(
        r.delta_catalog,
        "execute",
        lambda sql, label=None: queries.append(sql) or execute(sql, label=label),
    )
    download(r)
    assert not any("COUNT" in q for q in queries)  # read from the Delta log


def test_failed_count_downloads_without_total(make_rester, monkeypatch, caplog):
    r = make_rester(gnome=False)

    def fail(sql, label=None):
        raise RuntimeError("S3 timeout")

    monkeypatch.setattr(r.delta_catalog, "execute", fail)
    with caplog.at_level(logging.WARNING, logger="mp_api.client.core.client"):
        data = download(r)
    assert len(data) == 5
    assert "downloading without a total" in caplog.text


def test_status_helper_without_display_and_logger_is_silent(caplog):
    with caplog.at_level(logging.DEBUG):
        with display.status("quiet", enabled=False):
            pass
    assert caplog.text == ""


# --------------------------------------------------------------------------
# Log output after a download
# --------------------------------------------------------------------------


def info_messages(caplog) -> list[str]:
    return list(
        dict.fromkeys(  # caplog may hold a record twice, see above
            r.getMessage() for r in caplog.records if r.levelno >= logging.INFO
        )
    )


def test_path_shown_once_with_progress_bar(make_rester, term, caplog):
    r = make_rester()
    r.mute_progress_bars = False
    with caplog.at_level(logging.DEBUG, logger="mp_api.client.core.client"):
        download(r)

    out = plain(term.getvalue())
    assert "✓ Downloaded 6 Doc documents (v2026.09.28) to" in out
    assert not any("written to" in m for m in info_messages(caplog))
    debug = [r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("delta-rs and pyarrow documentation" in m for m in debug)


def test_path_logged_when_progress_muted(make_rester, caplog):
    with caplog.at_level(logging.INFO, logger="mp_api.client.core.client"):
        download(make_rester())  # muted: no summary line

    messages = info_messages(caplog)
    written = [m for m in messages if "written to" in m]
    assert len(written) == 1
    assert written[0].startswith("Dataset for chemenv (v2026.09.28) written to ")
    assert not any("delta-rs and pyarrow documentation" in m for m in messages)


def test_bar_replaced_by_status_while_committing(make_rester, term, monkeypatch):
    r = make_rester()
    r.mute_progress_bars = False
    commit = BaseRester._commit_delta_download
    seen = {}

    def spy(*args, **kwargs):
        tasks = display._STATE.progress.tasks
        seen["visible"] = [
            (t.description, bool(t.fields.get("status"))) for t in tasks if t.visible
        ]
        return commit(*args, **kwargs)

    monkeypatch.setattr(BaseRester, "_commit_delta_download", staticmethod(spy))
    download(r)

    # only the status line is visible during the commit, the bar is hidden
    assert len(seen["visible"]) == 1
    description, is_status = seen["visible"][0]
    assert is_status and "to the local DeltaTable" in description
    # the summary is still printed, after the commit
    assert "✓ Downloaded 6 Doc documents (v2026.09.28)" in plain(term.getvalue())
    assert display._STATE.progress is None


def test_hidden_bar_still_summarizes(term):
    with display.progress_bar("work", total=3, summary="Did {completed}") as bar:
        bar.update(3)
        bar.hide()
        assert not display._STATE.progress.tasks[0].visible
        bar.update(1)  # counted, not redrawn
        assert not display._STATE.progress.tasks[0].visible
    assert "✓ Did 4" in plain(term.getvalue())


# --------------------------------------------------------------------------
# Per-call db_version
# --------------------------------------------------------------------------


def test_per_call_version_does_not_change_rester(make_rester):
    r = make_rester()  # rester default: 2026.09.28 (heartbeat)
    old = r._query_resource(criteria={}, db_version="2026.04.13")["data"]
    current = download(r)

    assert (old.version, len(old)) == ("2026.04.13", 10)
    assert (current.version, len(current)) == ("2026.09.28", 6)
    assert r.db_version == "2026.09.28"


def test_search_passes_db_version(make_rester):
    data = make_rester()._search(db_version="2026-04-13")
    assert data.version == "2026.04.13" and len(data) == 10


@pytest.mark.parametrize("where", ["call", "rester"])
def test_latest_resolves_to_newest_partition(make_rester, monkeypatch, where):
    # The API still serves the older version, S3 already has a newer one
    monkeypatch.setattr(
        BaseRester,
        "_get_heartbeat_info",
        staticmethod(lambda endpoint: ("2026.04.13", ["gnome_r2scan_statics"])),
    )
    if where == "call":
        r = make_rester()
        data = r._query_resource(criteria={}, db_version="LATEST")["data"]
        assert r.db_version == "2026.04.13"
    else:
        r = make_rester(db_version="latest")
        assert r.db_version == "latest"
        data = download(r)
    assert data.version == "2026.09.28" and len(data) == 6


def test_missing_per_call_version(make_rester):
    with pytest.raises(MPRestError, match="2030.01.01 is not available"):
        make_rester()._query_resource(criteria={}, db_version="2030.01.01")


def test_filtered_query_with_other_version_raises(make_rester, monkeypatch):
    r = make_rester()
    monkeypatch.setattr(
        r, "_submit_requests", lambda **kw: pytest.fail("REST must not be queried")
    )
    with pytest.raises(MPRestError, match="only applies to full dataset downloads"):
        r._query_resource(criteria={"nsites_min": 1}, db_version="2026.04.13")


def test_filtered_query_with_current_version_goes_to_rest(make_rester, monkeypatch):
    r = make_rester()
    seen = {}
    monkeypatch.setattr(
        r, "_submit_requests", lambda **kw: seen.update(kw) or {"data": [], "meta": {}}
    )
    r._query_resource(criteria={"nsites_min": 1}, db_version="2026-09-28")
    assert seen["criteria"]["nsites_min"] == 1


def test_filtered_query_with_latest(make_rester, monkeypatch):
    r = make_rester()
    monkeypatch.setattr(r, "_submit_requests", lambda **kw: {"data": [], "meta": {}})
    # newest on S3 == the API's version -> fine
    r._query_resource(criteria={"nsites_min": 1}, db_version="latest")

    r.current_db_version = "2026.04.13"  # API behind S3 -> can't serve "latest"
    with pytest.raises(MPRestError, match="serves database version 2026.04.13"):
        r._query_resource(criteria={"nsites_min": 1}, db_version="latest")


def test_unversioned_dataset_ignores_per_call_version(
    make_rester, tmp_path, monkeypatch, caplog
):
    uri = str(tmp_path / "flat")
    write_deltalake(uri, remote_rows("x", 4).drop_columns(["version"]))
    point_at(monkeypatch, uri)
    with caplog.at_level(logging.WARNING, logger="mp_api.client.core.client"):
        data = make_rester()._query_resource(criteria={}, db_version="2026.04.13")
    assert len(data["data"]) == 4
    assert "has a single version, ignoring db_version='2026.04.13'" in caplog.text


def _route_classes():
    """Every rester class reachable from MPRester, keyed by suffix."""
    from mp_api.client.mprester import GENERIC_RESTERS, RESTER_LAYOUT

    classes = {}
    for lazy in (RESTER_LAYOUT | GENERIC_RESTERS).values():
        lazy._load()
        cls = lazy._imported
        if isinstance(cls, type) and issubclass(cls, BaseRester) and cls.suffix:
            classes[cls.suffix] = cls
    return classes


def _location(cls):
    return cls._s3_location(cls.__new__(cls))


@pytest.mark.parametrize(
    "suffix, bucket, prefix",
    [
        ("materials/summary", "materialsproject-build", "collections/summary"),
        ("materials/core", "materialsproject-build", "collections/materials"),
        (
            "materials/oxidation_states",
            "materialsproject-build",
            "collections/oxidation-states",
        ),
        ("materials/tasks", "materialsproject-parsed", "core/tasks"),
        ("materials/xas", "materialsproject-build", "static-collections/xas"),
        (
            "materials/surface_properties",
            "materialsproject-build",
            "static-collections/surface-properties",
        ),
        (
            "materials/grain_boundaries",
            "materialsproject-build",
            "static-collections/grain-boundaries",
        ),
        (
            "materials/synthesis",
            "materialsproject-build",
            "static-collections/synth-descriptions",
        ),
        ("materials/eos", "materialsproject-build", "static-collections/eos"),
        ("materials/phonon", "materialsproject-build", "static-collections/phonon"),
        ("molecules/summary", "materialsproject-build", "static-collections/molecules"),
        ("molecules/jcesr", "materialsproject-build", "static-collections/jcesr"),
    ],
)
def test_s3_locations(suffix, bucket, prefix):
    assert _location(_route_classes()[suffix])[1:] == (bucket, prefix)


@pytest.mark.parametrize(
    "suffix",
    [
        "materials/xas",
        "materials/surface_properties",
        "materials/grain_boundaries",
        "materials/synthesis",
    ],
)
def test_migrated_static_collections_are_delta_backed(suffix):
    assert _route_classes()[suffix].delta_backed


def test_db_version_only_on_versioned_routes():
    """`db_version` is offered by a route's search methods exactly when it can be
    honored: the route is delta-backed and its dataset lives under collections/
    (partitioned by version)."""
    wrong = []
    for suffix, cls in _route_classes().items():
        versioned = cls.delta_backed and _location(cls)[2].startswith("collections/")
        for name in ("search", "search_docs"):
            method = cls.__dict__.get(name) or next(
                (
                    b.__dict__[name]
                    for b in cls.__mro__[1:-1]
                    if name in b.__dict__ and b is not BaseRester
                ),
                None,
            )
            if method is None:
                continue
            source = inspect.getsource(method)
            if "_search(" not in source:
                continue  # e.g. text searches that never reach S3
            takes = "db_version" in inspect.signature(method).parameters
            passes = "db_version=db_version" in source
            if takes != versioned or passes != versioned:
                wrong.append(f"{suffix}.{name}: takes={takes} passes={passes}")
    assert not wrong
    assert "db_version" in inspect.signature(BaseRester._search).parameters


def test_phase_diagram_version(make_rester, monkeypatch):
    r = make_rester()
    queries = []
    monkeypatch.setattr(
        BaseRester,
        "_query_delta_single",
        lambda self, q, label=None: queries.append(q)
        or pa.table({"phase_diagram": []}),
    )
    from mp_api.client.routes.materials.thermo import ThermoRester

    thermo = ThermoRester.__new__(ThermoRester)
    thermo.__dict__.update(r.__dict__)
    thermo.get_phase_diagram_from_chemsys("O-Li")
    thermo.get_phase_diagram_from_chemsys("O-Li", db_version="2026.04.13")
    thermo.get_phase_diagram_from_chemsys("O-Li", db_version="latest")
    versions = [re.search(r"version='([^']+)'", q).group(1) for q in queries]
    assert versions == ["2026-09-28", "2026-04-13", "2026-09-28"]


# --------------------------------------------------------------------------
# MPRester.available_db_versions
# --------------------------------------------------------------------------


@pytest.fixture
def mpr(make_rester, tmp_path, remote, monkeypatch):
    from mp_api.client import MPRester

    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    flat = str(tmp_path / "flat")
    write_deltalake(flat, pa.table({"x": [1]}))

    def get_delta_table(
        self, bucket, prefix, connector="s3a", label=None, refresh=False
    ):
        if prefix.endswith("chemenv") or prefix.endswith("summary"):
            name = prefix.rsplit("/", 1)[-1]
            return self.delta_catalog.get_table(remote, name, refresh=refresh)
        if prefix.endswith("bonds"):
            return self.delta_catalog.get_table(flat, "bonds", refresh=refresh)
        raise FileNotFoundError(f"no table at {prefix}")

    monkeypatch.setattr(BaseRester, "_get_delta_table", get_delta_table)
    return MPRester(api_key="a" * 32, mute_progress_bars=True)


def test_mprester_lists_all_versioned_collections(mpr):
    assert mpr.available_db_versions() == {
        # same remote table used for both; bonds (unversioned) and
        # collections that fail to load are left out
        "chemenv": ["2026.04.13", "2026.09.28"],
        "summary": ["2026.04.13", "2026.09.28"],
    }


def test_mprester_skips_unversioned_routes_without_importing(mpr):
    routes = set(mpr._versioned_resters())
    assert not routes & {"tasks", "similarity", "synthesis", "eos", "phonon", "xas"}
    assert {"summary", "chemenv", "thermo"} <= routes


@pytest.mark.parametrize("name", ["summary", "materials/summary"])
def test_mprester_single_collection(mpr, name):
    assert mpr.available_db_versions(name) == ["2026.04.13", "2026.09.28"]


def test_mprester_unknown_collection(mpr):
    with pytest.raises(MPRestError, match="Unknown collection 'nope'"):
        mpr.available_db_versions("nope")


def test_mprester_listing_shows_status(mpr, term, monkeypatch):
    mpr.mute_progress_bars = False
    calls = []
    original = BaseRester.available_db_versions

    def spy(self):
        tasks = display._STATE.progress.tasks
        calls.append([t.description for t in tasks if t.fields.get("status")])
        return original(self)

    monkeypatch.setattr(BaseRester, "available_db_versions", spy)
    mpr.available_db_versions()
    assert calls and all(
        any("Fetching available database versions" in d for d in c) for c in calls
    )
    assert display._STATE.progress is None


def test_mprester_latest_repr_and_warning(make_rester, monkeypatch, caplog):
    from mp_api.client import MPRester

    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    with caplog.at_level(logging.WARNING, logger="mp_api.client.mprester"):
        m = MPRester(api_key="a" * 32, db_version="Latest")
    assert repr(m) == "MPRester(latest)"
    assert m.materials.summary.db_version == "latest"
    assert "newest database version on S3" in caplog.text


# --------------------------------------------------------------------------
# Static collections: unversioned, partitioned by other columns
# --------------------------------------------------------------------------


class EdgeDoc(BaseModel):
    material_id: str
    edge: str
    absorbing_element: str


class EdgeRester(BaseRester):
    suffix = "materials/xas"
    document_model = EdgeDoc


def test_static_collection_partitioned_by_other_columns(
    make_rester, tmp_path, monkeypatch
):
    uri = str(tmp_path / "xas")
    write_deltalake(
        uri,
        pa.table(
            {
                "material_id": ["mp-1", "mp-2", "mp-3"],
                "edge": ["K", "L3", "K"],
                "absorbing_element": ["Fe", "Fe", "O"],
            }
        ),
        partition_by=["edge"],
    )
    point_at(monkeypatch, uri)
    make_rester()  # patches the GNoMe check and heartbeat
    r = EdgeRester(
        api_key="a" * 32,
        local_dataset_cache=tmp_path / "cache",
        mute_progress_bars=True,
    )
    data = r._query_resource(criteria={})["data"]

    assert data.version is None and len(data) == 3
    table = data.pyarrow_dataset.to_table()
    assert sorted(table["edge"].to_pylist()) == ["K", "K", "L3"]  # kept as a column
    local = DeltaTable(str(tmp_path / "cache" / "build" / "static-collections" / "xas"))
    assert local.metadata().partition_columns == []


def test_synthesis_downloads_recipes(make_rester, tmp_path, monkeypatch):
    from emmet.core.arrow import arrowize
    from emmet.core.synthesis import SynthesisRecipe

    from mp_api.client.routes.materials.synthesis import SynthesisRester

    schema = pa.schema(arrowize(SynthesisRecipe))
    assert "search_score" not in schema.names and "highlights" not in schema.names
    uri = str(tmp_path / "synth")
    write_deltalake(uri, schema.empty_table(), partition_by=["synthesis_type"])
    point_at(monkeypatch, uri)
    make_rester()
    r = SynthesisRester(
        api_key="a" * 32,
        local_dataset_cache=tmp_path / "cache",
        mute_progress_bars=True,
    )
    assert r._download_schema() == schema

    calls = []
    monkeypatch.setattr(
        BaseRester,
        "_query_delta_backed",
        lambda self, **kw: calls.append(kw) or {"data": "downloaded"},
    )
    assert r.search() == "downloaded"  # no search terms: full download
    assert calls[0]["prefix"] == "static-collections/synth-descriptions"

    monkeypatch.setattr(
        BaseRester,
        "_submit_requests",
        lambda self, **kw: {"data": ["rest"], "meta": {}},
    )
    assert r.search(keywords=["silicon"]) == ["rest"]  # text search stays on REST
    assert len(calls) == 1
