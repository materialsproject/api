"""Progress bar behaviour of the core client, without network access."""

import io
import re

import pytest
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client.core.client import BaseRester
from mp_api.client.core.exceptions import MPRestError


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


@pytest.fixture
def term():
    buf = io.StringIO()
    display.set_console(
        Console(file=buf, force_terminal=True, force_jupyter=False, width=120)
    )
    yield buf
    display.set_console(None)


@pytest.fixture
def rester(monkeypatch):
    monkeypatch.setattr(
        BaseRester, "_get_heartbeat_info", staticmethod(lambda endpoint: ("v", []))
    )
    return BaseRester(api_key="a" * 32)


def fake_pages(total: int, fail_on_call: int | None = None):
    """Stand-in for _submit_request_and_process serving `total` docs."""
    calls = {"n": 0}

    def submit(url, verify, params, use_document_model, timeout=None):
        calls["n"] += 1
        if fail_on_call is not None and calls["n"] == fail_on_call:
            raise MPRestError("REST query timed out")
        limit = params.get("_limit", 10)
        skip = params.get("_skip", 0)
        n = max(0, min(limit, total - skip))
        return {"data": [{"i": skip + j} for j in range(n)], "meta": {}}, total

    return submit, calls


def test_pagination_shows_bar_and_summary(rester, term, monkeypatch):
    submit, calls = fake_pages(25)
    monkeypatch.setattr(rester, "_submit_request_and_process", submit)

    out = rester._submit_requests(
        url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
    )

    assert len(out["data"]) == 25 and calls["n"] == 3
    assert "✓ Retrieved 25 documents in" in plain(term.getvalue())
    assert display._STATE.progress is None


def test_bar_starts_before_first_request(rester, term, monkeypatch):
    """The spinner is visible while the first (often slowest) request runs."""
    submit, _ = fake_pages(5)

    def spy(*args, **kwargs):
        assert display._STATE.active == 1
        assert display._STATE.progress.tasks[0].total is None  # not known yet
        return submit(*args, **kwargs)

    monkeypatch.setattr(rester, "_submit_request_and_process", spy)
    rester._submit_requests(
        url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
    )
    assert "✓ Retrieved 5 documents in" in plain(term.getvalue())


def test_empty_result_has_no_summary(rester, term, monkeypatch):
    submit, _ = fake_pages(0)
    monkeypatch.setattr(rester, "_submit_request_and_process", submit)
    rester._submit_requests(
        url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
    )
    assert "Retrieved" not in plain(term.getvalue())
    assert display._STATE.progress is None


def test_bar_closed_when_first_request_fails(rester, term, monkeypatch):
    submit, _ = fake_pages(25, fail_on_call=1)
    monkeypatch.setattr(rester, "_submit_request_and_process", submit)
    with pytest.raises(MPRestError):
        rester._submit_requests(
            url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
        )
    assert display._STATE.progress is None and display._STATE.active == 0


def test_show_progress_false_and_mute_are_silent(rester, term, monkeypatch):
    submit, _ = fake_pages(25)
    monkeypatch.setattr(rester, "_submit_request_and_process", submit)
    kwargs = dict(
        url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
    )

    rester._submit_requests(**kwargs, show_progress=False)
    assert term.getvalue() == ""

    rester.mute_progress_bars = True
    rester._submit_requests(**kwargs)
    assert term.getvalue() == ""

    # explicit True overrides the instance setting
    rester._submit_requests(**kwargs, show_progress=True)
    assert "Retrieved 25" in plain(term.getvalue())


def test_bar_closed_when_page_request_fails(rester, term, monkeypatch):
    submit, _ = fake_pages(25, fail_on_call=2)
    monkeypatch.setattr(rester, "_submit_request_and_process", submit)

    with pytest.raises(MPRestError, match="timed out"):
        rester._submit_requests(
            url="u", criteria={"_limit": 10}, use_document_model=False, chunk_size=10
        )

    assert display._STATE.progress is None
    assert display._STATE.active == 0
    assert "Retrieved" not in term.getvalue()


def test_split_batches_nest_without_error(rester, term, monkeypatch):
    """A 414 splits the query into batches whose pagination bars nest under it."""
    values = [f"mp-{i}" for i in range(250)]

    def submit(url, verify, params, use_document_model, timeout=None):
        ids = params["material_ids"].split(",")
        if len(ids) > 100:
            raise MPRestError("REST query returned with error status code 414")
        skip, limit = params.get("_skip", 0), params.get("_limit", 50)
        page = ids[skip : skip + limit]
        return {
            "data": [{"id": i} for i in page],
            "meta": {"total_doc": len(ids)},
        }, len(ids)

    monkeypatch.setattr(rester, "_submit_request_and_process", submit)
    out = rester._submit_requests(
        url="u",
        criteria={"material_ids": ",".join(values), "_limit": 50},
        use_document_model=False,
        chunk_size=50,
    )

    assert len(out["data"]) == 250
    text = plain(term.getvalue())
    # one summary, for the outer batching bar; total is ceil(250/100) = 3
    assert "✓ Retrieved 250 material_ids values in 3 batches" in text
    assert "Retrieved 100 documents" not in text
    assert display._STATE.progress is None


def test_count_failure_does_not_leave_rester_muted(rester, monkeypatch):
    def boom(*args, **kwargs):
        assert kwargs["show_progress"] is False
        assert kwargs["use_document_model"] is False
        raise MPRestError("network down")

    monkeypatch.setattr(rester, "_query_resource", boom)
    rester.mute_progress_bars = False
    rester.use_document_model = True

    with pytest.raises(MPRestError):
        rester.count()

    assert rester.mute_progress_bars is False
    assert rester.use_document_model is True
