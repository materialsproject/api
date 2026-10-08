"""Progress and messaging for client-side entry processing. No network access.

Covers `core/_entries.py` (rescaling to conventional cells, corrections and the
GGA(+U)/r2SCAN mixing scheme behind a progress bar) and how MPRester's entry
methods use it, with the API mocked out.
"""

import io
import logging
import re
import warnings

import pytest
from pymatgen.core import Lattice, Structure
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.entries.computed_entries import (
    ComputedStructureEntry,
    GibbsComputedStructureEntry,
)
from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme
from rich.console import Console

import mp_api.client.core._display as display
from mp_api.client import quiet
from mp_api.client.core._display import MP_THEME, progress_bar
from mp_api.client.core._entries import (
    _track_calls,
    apply_corrections,
    _private_copy,
    get_conventional_cell_entry,
    rescale_to_conventional,
)
from mp_api.client.core.exceptions import MPRestWarning

CLIENT = "mp_api.client"


def messages(caplog) -> list[str]:
    """Distinct messages; caplog can see a record twice (root handler and ours)."""
    return list({id(r): r.getMessage() for r in caplog.records}.values())


@pytest.fixture
def term():
    buf = io.StringIO()
    display.set_console(
        Console(
            file=buf,
            force_terminal=True,
            force_jupyter=False,
            width=140,
            theme=MP_THEME,
        )
    )
    yield buf
    display.set_console(None)


@pytest.fixture
def pipe():
    buf = io.StringIO()
    display.set_console(Console(file=buf, force_terminal=False, force_jupyter=False))
    yield buf
    display.set_console(None)


def plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


def _entry(entry_id, run_type, species, coords, a, energy_per_atom, cubic="P"):
    lattice = Lattice.cubic(a)
    if cubic == "F":  # primitive fcc cell: 4x fewer sites than conventional
        lattice = Lattice.from_parameters(a, a, a, 60, 60, 60)
    structure = Structure(lattice, species, coords)
    return ComputedStructureEntry(
        structure,
        energy_per_atom * len(structure),
        parameters={
            "run_type": run_type,
            "hubbards": {},
            "is_hubbard": False,
            "potcar_symbols": [],
        },
        entry_id=entry_id,
    )


def li_o_entries():
    """Small, complete GGA and r2SCAN Li-O systems, enough for the mixing scheme."""
    entries = []
    for run_type, shift in (("GGA", 0.0), ("r2SCAN", -1.0)):
        entries += [
            _entry(f"{run_type}-1", run_type, ["Li"], [[0, 0, 0]], 3.4, -1.9 + shift),
            _entry(
                f"{run_type}-2",
                run_type,
                ["O", "O"],
                [[0, 0, 0], [0.5, 0.5, 0.5]],
                4.0,
                -4.9 + shift,
            ),
            _entry(
                f"{run_type}-3",
                run_type,
                ["Li", "Li", "O"],
                [[0, 0, 0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
                4.6,
                -4.8 + shift,
            ),
            _entry(
                f"{run_type}-4",
                run_type,
                ["Li", "O"],
                [[0, 0, 0], [0.5, 0.5, 0.5]],
                3.0,
                -4.0 + shift,
            ),
        ]
    return entries


def mixing_scheme(**kwargs):
    # synthetic entries carry no POTCAR info
    return MaterialsProjectDFTMixingScheme(
        compat_1=MaterialsProject2020Compatibility(check_potcar=False),
        check_potcar=False,
        **kwargs,
    )


def fcc_entry(material_id="mp-1"):
    return _entry(
        f"{material_id}-GGA", "GGA", ["Cu"], [[0, 0, 0]], 3.6, -3.7, cubic="F"
    )


# --- _track_calls ------------------------------------------------------------------


def test_track_calls_counts_and_restores():
    class Obj:
        def work(self, items):
            return len(items)

    obj = Obj()
    handle = display.ProgressHandle(total=10)
    with _track_calls(obj, "work", handle, lambda items: len(items)):
        assert obj.work([1, 2, 3]) == 3
        assert obj.work([1]) == 1
    assert handle.completed == 4
    assert "work" not in vars(obj)  # instance attribute removed again
    assert Obj.work.__qualname__.endswith("Obj.work")  # class untouched


def test_track_calls_never_passes_total():
    class Obj:
        def work(self):
            return None

    obj = Obj()
    handle = display.ProgressHandle(total=2)
    with _track_calls(obj, "work", handle):
        for _ in range(5):
            obj.work()
    assert handle.completed == 2


def test_track_calls_counts_calls_that_raise():
    class Obj:
        def work(self):
            raise ValueError

    obj = Obj()
    handle = display.ProgressHandle(total=2)
    with _track_calls(obj, "work", handle):
        with pytest.raises(ValueError):
            obj.work()
    assert handle.completed == 1


def test_track_calls_restores_on_error_and_keeps_own_attribute():
    class Obj:
        pass

    obj = Obj()
    obj.work = lambda: 1 / 0  # an instance attribute already
    original = obj.work
    with pytest.raises(ZeroDivisionError):
        with _track_calls(obj, "work", display.ProgressHandle(total=1)):
            obj.work()
    assert obj.work is original


def test_private_copy_bypasses_pymatgen_instance_cache():
    shared = MaterialsProject2020Compatibility()
    assert MaterialsProject2020Compatibility() is shared  # monty @cached_class
    clone = _private_copy(shared)
    assert clone is not shared and type(clone) is type(shared)
    clone.get_adjustments = None
    assert "get_adjustments" not in vars(shared)
    assert MaterialsProject2020Compatibility() is shared  # cache untouched


# --- results are unchanged ---------------------------------------------------------


def test_mixing_results_identical_with_progress(term):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        expected = mixing_scheme().process_entries(li_o_entries())
        scheme = mixing_scheme()
        processed = apply_corrections(
            scheme,
            li_o_entries(),
            description="Re-mixing",
            log="Re-mixing",
            summary="Re-mixed 8 entries ({kept:,} kept)",
        )
    assert [(e.entry_id, e.energy) for e in processed] == pytest.approx(
        [(e.entry_id, e.energy) for e in expected]
    )
    # the caller's scheme and its parts were never modified
    for obj in (scheme, scheme.compat_1, scheme.structure_matcher):
        assert not {"get_adjustments", "group_structures"} & set(vars(obj))
    assert MaterialsProject2020Compatibility(check_potcar=False) is scheme.compat_1
    out = plain(term.getvalue())
    assert f"Re-mixed 8 entries ({len(expected)} kept)" in out


def test_mixing_bar_counts_passes(monkeypatch):
    """The counted passes add up to the number of entries without the final top-up."""
    seen = []
    real_advance = display.ProgressHandle.update

    def record(self, advance=1):
        seen.append(advance)
        real_advance(self, advance)

    monkeypatch.setattr(display.ProgressHandle, "update", record)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        apply_corrections(
            mixing_scheme(), li_o_entries(), description="x", log="x", summary="x"
        )
    # the counted calls cover most of the work (O2's structures are grouped by
    # pymatgen without the structure matcher, so they're filled in at the end)
    counted = sum(seen[:-1])
    assert 0.8 * 8 <= counted < 8
    assert sum(seen) == pytest.approx(8)


def test_compatibility_corrections_counted(term, monkeypatch):
    entries = [e for e in li_o_entries() if e.parameters["run_type"] == "GGA"]
    compat = MaterialsProject2020Compatibility(check_potcar=False)
    calls = []
    real = MaterialsProject2020Compatibility.get_adjustments

    def spy(self, entry):
        calls.append(entry.entry_id)
        return real(self, entry)

    monkeypatch.setattr(MaterialsProject2020Compatibility, "get_adjustments", spy)
    processed = apply_corrections(
        compat,
        entries,
        description="Correcting",
        log="Correcting",
        summary="Corrected 4 entries ({kept:,} kept)",
    )
    assert len(calls) == 4 and len(processed) == 4
    assert "get_adjustments" not in vars(compat)
    assert "Corrected 4 entries (4 kept)" in plain(term.getvalue())


def test_rescale_matches_per_entry_function(term):
    entry = fcc_entry()
    [rescaled] = rescale_to_conventional([entry])
    direct = get_conventional_cell_entry(entry)
    assert len(rescaled.structure) == len(direct.structure) == 4
    assert rescaled.energy_per_atom == pytest.approx(entry.energy_per_atom)
    out = plain(term.getvalue())
    assert "Rescaled 1 entry to conventional unit cells" in out


# --- progress_bar additions --------------------------------------------------------


def test_progress_bar_log_when_not_drawable(pipe, caplog):
    with caplog.at_level(logging.INFO, logger=CLIENT):
        with progress_bar("x", total=1, log="Doing the thing") as handle:
            handle.update()
    assert messages(caplog) == ["Doing the thing"]
    assert pipe.getvalue() == ""


@pytest.mark.parametrize("muted", [True, False])
def test_progress_bar_log_silent_when_muted_or_quiet(pipe, caplog, muted):
    with caplog.at_level(logging.DEBUG, logger=CLIENT):
        if muted:
            with progress_bar("x", total=1, log="msg", enabled=False):
                pass
        else:
            with quiet(), progress_bar("x", total=1, log="msg"):
                pass
    assert not caplog.records


def test_progress_bar_summary_can_be_replaced(term):
    with progress_bar("x", total=2, summary="placeholder") as handle:
        handle.update(2)
        handle.summary = "Done {completed} of {total}, {{literal}}"
    assert "Done 2 of 2, {literal}" in plain(term.getvalue())


# --- MPRester entry methods --------------------------------------------------------


@pytest.fixture
def mpr(monkeypatch):
    from mp_api.client import MPRester
    from mp_api.client.core.client import _Rester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    return MPRester(api_key="a" * 32)


@pytest.fixture
def thermo(monkeypatch):
    """Patch `ThermoRester` methods (MPRester's resters are lazy wrappers)."""
    from mp_api.client.routes.materials.thermo import ThermoRester

    def patch(name, func):
        monkeypatch.setattr(ThermoRester, name, func)

    return patch


def _thermo_docs(entries):
    return [
        {
            "entries": {"GGA": e.as_dict()},
            "thermo_type": "GGA_GGA+U",
            "material_id": e.entry_id,
        }
        for e in entries
    ]


def test_get_entries_conventional_shows_progress(mpr, thermo, term):
    entries = [fcc_entry("mp-1"), fcc_entry("mp-2")]
    thermo("search", lambda self, **kw: _thermo_docs(entries))
    result = mpr.get_entries(["mp-1", "mp-2"], conventional_unit_cell=True)
    assert sorted(len(e.structure) for e in result) == [4, 4]
    assert "Rescaled 2 entries to conventional unit cells" in plain(term.getvalue())


def test_get_entries_conventional_logs_in_scripts(mpr, thermo, pipe, caplog):
    thermo("search", lambda self, **kw: _thermo_docs([fcc_entry()]))
    with caplog.at_level(logging.INFO, logger=CLIENT):
        mpr.get_entries("mp-1", conventional_unit_cell=True)
    assert "Rescaling 1 entry to conventional unit cells" in messages(caplog)


def test_get_entries_conventional_silent_when_muted(mpr, thermo, pipe, caplog):
    mpr.mute_progress_bars = True
    thermo("search", lambda self, **kw: _thermo_docs([fcc_entry()]))
    with caplog.at_level(logging.DEBUG, logger=CLIENT):
        mpr.get_entries("mp-1", conventional_unit_cell=True)
    assert not caplog.records and pipe.getvalue() == ""


def test_remix_without_prebuilt_pd(mpr, thermo, monkeypatch, term, caplog):
    """No pre-built PD: a log warning (not MPRestWarning) and a re-mixing bar."""
    thermo("get_phase_diagram_from_chemsys", lambda self, *a, **k: None)
    monkeypatch.setattr(
        type(mpr), "_get_unmixed_entries", lambda self, *a, **k: li_o_entries()
    )
    real_init = MaterialsProjectDFTMixingScheme.__init__

    def init(self, **kw):  # synthetic entries carry no POTCAR info
        kw.setdefault("compat_1", MaterialsProject2020Compatibility(check_potcar=False))
        real_init(self, check_potcar=False, **kw)

    monkeypatch.setattr(MaterialsProjectDFTMixingScheme, "__init__", init)
    with (
        warnings.catch_warnings(record=True) as record,
        caplog.at_level(logging.INFO, logger=CLIENT),
    ):
        warnings.simplefilter("always")
        entries = mpr.get_entries_in_chemsys(
            "Li-O", additional_criteria={"thermo_types": ["GGA_GGA+U_R2SCAN"]}
        )
    assert entries
    assert not [w for w in record if issubclass(w.category, MPRestWarning)]
    assert any(
        "no pre-built phase diagram for Li-O" in r.getMessage()
        for r in caplog.records
        if r.levelno == logging.WARNING
    )
    out = plain(term.getvalue())
    assert f"Re-mixed 8 entries onto a common energy scale ({len(entries)} kept)" in out


def test_gibbs_conversion_shows_status(mpr, pipe, caplog):
    entries = [e for e in li_o_entries() if e.parameters["run_type"] == "GGA"]
    with caplog.at_level(logging.INFO, logger=CLIENT):
        gibbs = mpr._to_gibbs_entries(entries, 300)
    assert gibbs and all(isinstance(e, GibbsComputedStructureEntry) for e in gibbs)
    assert "Estimating Gibbs free energies at 300 K for 4 entries..." in messages(
        caplog
    )


def test_get_stability_shows_progress(mpr, thermo, monkeypatch, term):
    from pymatgen.analysis.phase_diagram import PhaseDiagram

    gga = [e for e in li_o_entries() if e.parameters["run_type"] == "GGA"]
    thermo(
        "get_phase_diagram_from_chemsys", lambda self, *a, **k: PhaseDiagram(gga[:3])
    )
    monkeypatch.setattr(
        "pymatgen.entries.compatibility.MaterialsProject2020Compatibility",
        lambda: MaterialsProject2020Compatibility(check_potcar=False),
    )
    mine = [gga[3]]
    result = mpr.get_stability(mine, thermo_type="GGA_GGA+U")
    assert result and result[0]["entry_id"] == "GGA-4"
    assert "Corrected 4 entries (4 kept)" in plain(term.getvalue())
