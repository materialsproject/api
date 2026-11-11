"""Messages and status lines of the electronic structure shortcuts. No network access."""

import io
import logging

import pytest
from emmet.core.band_theory import BSPathType
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client.core.exceptions import MPRestError
from mp_api.client.routes.materials.electronic_structure import (
    BandStructureRester,
    DosRester,
    ElectronicStructureRester,
)


def _summary(bandstructure=None, dos=None):
    return [{"material_id": "mp-x", "bandstructure": bandstructure, "dos": dos}]


@pytest.fixture
def make(monkeypatch):
    """A rester whose electronic structure lookup returns `docs`."""

    def build(cls, docs):
        class FakeES:
            @staticmethod
            def search(material_ids, fields):
                return docs

        rester = cls(api_key="a" * 32, use_document_model=False)
        monkeypatch.setattr(cls, "es_rester", FakeES())
        monkeypatch.setattr(
            rester,
            "get_bandstructure_from_task_id",
            lambda *a, **k: "bs",
            raising=False,
        )
        monkeypatch.setattr(
            rester, "get_dos_from_task_id", lambda *a, **k: "dos", raising=False
        )
        return rester

    return build


# --- the path types a material has ----------------------------------------------


def test_missing_path_type_lists_the_available_ones(make):
    rester = make(
        BandStructureRester,
        _summary(
            bandstructure={
                "setyawan_curtarolo": {"task_id": "mp-1"},
                "hinuma": None,
                "latimer_munro": {"task_id": "mp-2"},
            }
        ),
    )
    with pytest.raises(MPRestError) as excinfo:
        rester.get_bandstructure_from_material_id("mp-x", path_type="hinuma")
    message = str(excinfo.value)
    assert "No hinuma band structure data found for mp-x" in message
    assert "available: latimer_munro, setyawan_curtarolo" in message


def test_missing_path_type_without_alternatives(make):
    rester = make(
        BandStructureRester, _summary(bandstructure={"setyawan_curtarolo": None})
    )
    with pytest.raises(MPRestError) as excinfo:
        rester.get_bandstructure_from_material_id("mp-x")
    assert str(excinfo.value) == (
        "No setyawan_curtarolo band structure data found for mp-x."
    )


def test_available_path_type_is_fetched(make):
    rester = make(
        BandStructureRester,
        _summary(bandstructure={"hinuma": {"task_id": "mp-1"}}),
    )
    assert (
        rester.get_bandstructure_from_material_id("mp-x", path_type=BSPathType.hinuma)
        == "bs"
    )


# --- task ID messages ------------------------------------------------------------


def _empty_table(monkeypatch, cls):
    class Empty:
        @staticmethod
        def to_pylist(**kwargs):
            return []

    rester = cls(api_key="a" * 32)
    monkeypatch.setattr(rester, "_get_delta_table", lambda *a, **k: ("lbl", None))
    monkeypatch.setattr(rester, "_query_delta_single", lambda *a, **k: Empty())
    return rester


def test_bandstructure_task_id_message_has_separators(monkeypatch):
    rester = _empty_table(monkeypatch, BandStructureRester)
    with pytest.raises(MPRestError) as excinfo:
        rester.get_bandstructure_from_task_id(
            "mp-1", run_type="GGA", path_type="hinuma"
        )
    assert str(excinfo.value) == (
        "No bandstructure data found for task_id='mp-1' and run_type=GGA "
        "and path_type=hinuma"
    )


def test_bandstructure_task_id_message_without_options(monkeypatch):
    rester = _empty_table(monkeypatch, BandStructureRester)
    with pytest.raises(MPRestError) as excinfo:
        rester.get_bandstructure_from_task_id("mp-1")
    assert str(excinfo.value) == "No bandstructure data found for task_id='mp-1'"


def test_dos_task_id_message_has_separator(monkeypatch):
    rester = _empty_table(monkeypatch, DosRester)
    with pytest.raises(MPRestError) as excinfo:
        rester.get_dos_from_task_id("mp-1", run_type="GGA")
    assert str(excinfo.value) == "No DOS data found for task_id='mp-1' and run_type=GGA"


# --- status lines ----------------------------------------------------------------


@pytest.fixture
def caplog():
    """Records that reach the application's root handlers (a plain recorder:
    pytest's own handlers would see the client's records more than once)."""
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


def _statuses(rester_call, records):
    display.set_console(Console(file=io.StringIO(), force_terminal=False))
    try:
        rester_call()
    finally:
        display.set_console(None)
    return [r.getMessage() for r in records if r.name == "mp_api.client"]


def test_bandstructure_shows_one_status_line(make, caplog):
    rester = make(
        BandStructureRester, _summary(bandstructure={"hinuma": {"task_id": "mp-1"}})
    )
    messages = _statuses(
        lambda: rester.get_bandstructure_from_material_id("mp-x", path_type="hinuma"),
        caplog,
    )
    assert messages == ["Fetching the hinuma band structure for mp-x..."]


def test_uniform_bandstructure_status_line(make, caplog):
    rester = make(BandStructureRester, _summary(dos={"total": {}, "task_id": "mp-1"}))
    messages = _statuses(
        lambda: rester.get_bandstructure_from_material_id("mp-x", line_mode=False),
        caplog,
    )
    assert messages == ["Fetching the uniform band structure for mp-x..."]


def test_dos_shows_one_status_line(make, caplog):
    rester = make(DosRester, _summary(dos={"task_id": "mp-1"}))
    messages = _statuses(lambda: rester.get_dos_from_material_id("mp-x"), caplog)
    assert messages == ["Fetching the density of states for mp-x..."]


def test_task_id_calls_show_their_own_status_line(monkeypatch, caplog):
    rester = _empty_table(monkeypatch, DosRester)

    def call():
        with pytest.raises(MPRestError):
            rester.get_dos_from_task_id("mp-1")

    assert _statuses(call, caplog) == ["Fetching the density of states for mp-1..."]


def test_muted_progress_bars_show_no_status_line(make, caplog):
    rester = make(DosRester, _summary(dos={"task_id": "mp-1"}))
    rester.mute_progress_bars = True
    assert _statuses(lambda: rester.get_dos_from_material_id("mp-x"), caplog) == []


def test_es_rester_is_unaffected():
    assert ElectronicStructureRester.suffix == "materials/electronic_structure"
