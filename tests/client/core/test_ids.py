"""ID validation and `get_entries` input handling. No network access."""

import warnings

import pytest

from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.client.core.utils import validate_ids


def caught(fn, *args, **kwargs):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        result = fn(*args, **kwargs)
    return result, [w for w in record if issubclass(w.category, MPRestWarning)]


def test_valid_ids_unchanged():
    ids = ["mp-149", "149", "mp-aaaaaaft", "aaabivno"]
    result, record = caught(validate_ids, ids)
    assert result == ["mp-149", "149", "mp-149", "612132"]
    assert not record


def test_molecule_ids_valid():
    """`mol-` IDs are valid (needs emmet-core with "mol" in STRICT_ID_PREFIXES)."""
    result, record = caught(validate_ids, ["mol-45228"])
    assert result == ["mol-45228"] and not record


def test_invalid_ids_warn_and_are_dropped():
    result, record = caught(validate_ids, ["mp-149", "fake-149", "x_y", "149"])
    assert result == ["mp-149", "149"]
    assert len(record) == 1
    message = str(record[0].message)
    assert "Ignoring invalid IDs" in message
    assert "'fake-149': prefix 'fake'" in message and "'x_y'" in message
    assert record[0].filename == __file__  # points at the caller


def test_legacy_ids_get_their_own_notice():
    result, record = caught(validate_ids, ["mvc-149", "mp-149"])
    assert result == ["mp-149"]
    assert [str(w.message) for w in record] == [
        "These IDs refer to legacy calculations that have been removed from the "
        "Materials Project database, and are ignored: mvc-149"
    ]


def test_no_valid_ids_raises():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(MPRestError, match=r"No valid IDs to query \(ignored: "):
            validate_ids(["mvc-1", "fake-2"])


def test_non_strings_are_invalid():
    result, record = caught(validate_ids, [149, "mp-13"])
    assert result == ["mp-13"] and "expected a string" in str(record[0].message)


def test_api_returned_ids_raise_instead_of_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # no warning either
        assert validate_ids(["mp-149"], user_input=False) == ["mp-149"]
        with pytest.raises(MPRestError, match="API returned invalid identifiers"):
            validate_ids(["mp-149", "fake-1"], user_input=False)
        with pytest.raises(MPRestError, match="mvc-1"):
            validate_ids(["mvc-1"], user_input=False)


def test_too_many_ids_raise():
    from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS

    with pytest.raises(MPRestError, match="too long"):
        validate_ids(["mp-1"] * (MAPI_CLIENT_SETTINGS.MAX_LIST_LENGTH + 1))


def test_quiet_silences_id_warnings():
    from mp_api.client import quiet

    with quiet():
        result, record = caught(validate_ids, ["mvc-1", "fake-2", "mp-3"])
    assert result == ["mp-3"] and not record


def test_rester_warning_points_at_user_code(monkeypatch):
    from mp_api.client.core.client import BaseRester, _Rester
    from mp_api.client.routes.materials.thermo import ThermoRester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    seen = {}
    monkeypatch.setattr(BaseRester, "_search", lambda self, **kw: seen.update(kw) or [])
    rester = ThermoRester(api_key="a" * 32)
    _, record = caught(rester.search, material_ids=["mp-149", "fake-1"])
    assert seen["material_ids"] == "mp-149"
    assert record[0].filename == __file__


# --- get_entries --------------------------------------------------------------


def test_classify_inputs():
    from mp_api.client.mprester import _classify_chemsys_formula_ids

    assert _classify_chemsys_formula_ids(
        ["Li-Fe-O", "Si-*", "Fe2O3", "Si*", "O", "mp-149", "mvc-149", "149", "Fe-x"]
    ) == {
        "chemsys": ["Li-Fe-O", "Si-*"],
        "formula": ["Fe2O3", "Si*", "O"],
        "material_ids": ["mp-149", "mvc-149", "149", "Fe-x"],
    }
    assert _classify_chemsys_formula_ids(["Fe2O3"]) == {"formula": ["Fe2O3"]}


@pytest.fixture
def mpr_and_queries(monkeypatch):
    from mp_api.client import MPRester
    from mp_api.client.core.client import _Rester
    from mp_api.client.routes.materials.thermo import ThermoRester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    queries: list[dict] = []

    def search(self, **kwargs):
        queries.append(kwargs)
        return []

    monkeypatch.setattr(ThermoRester, "search", search)
    return MPRester(api_key="a" * 32, mute_progress_bars=True), queries


def test_get_entries_one_query_per_kind(mpr_and_queries):
    mpr, queries = mpr_and_queries
    _, record = caught(
        mpr.get_entries,
        ["Li-O", "Fe2O3", "mp-149", "mvc-149"],
        additional_criteria={"is_stable": True},
    )
    assert [
        {k: v for k, v in q.items() if k not in {"fields", "all_fields"}}
        for q in queries
    ] == [
        {"chemsys": ["Li-O"], "is_stable": True},
        {"formula": ["Fe2O3"], "is_stable": True},
        {"material_ids": ["mp-149"], "is_stable": True},
    ]
    assert len(record) == 1 and "mvc-149" in str(record[0].message)
    assert record[0].filename == __file__


def test_get_entries_never_sends_ids_as_chemsys(mpr_and_queries):
    mpr, queries = mpr_and_queries
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(MPRestError, match="No valid IDs"):
            mpr.get_entries(["mvc-149", "mp-149-GGA"])
    assert queries == []


def test_get_entries_merges_and_deduplicates(mpr_and_queries, monkeypatch):
    from tests.client.test_entry_progress import _thermo_docs, fcc_entry

    from mp_api.client.routes.materials.thermo import ThermoRester

    shared = fcc_entry("mp-1")
    by_kind = {
        "chemsys": _thermo_docs([shared, fcc_entry("mp-2")]),
        "material_ids": _thermo_docs([shared]),
    }
    monkeypatch.setattr(
        ThermoRester,
        "search",
        lambda self, **kw: by_kind[next(k for k in by_kind if k in kw)],
    )
    mpr, _ = mpr_and_queries
    entries = mpr.get_entries(["Cu-Al", "mp-1"])
    assert sorted(str(e.entry_id) for e in entries) == ["mp-1-GGA", "mp-2-GGA"]


def test_messages_are_bounded():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        with pytest.raises(MPRestError) as error:
            validate_ids([f"bad_{i}" for i in range(500)])
    assert "(490 more)" in str(error.value) and len(str(error.value)) < 300
    assert "(490 more)" in str(record[0].message)
