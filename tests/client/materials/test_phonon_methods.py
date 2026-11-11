"""Choosing the phonon method for a material. No network access.

The summary lookup (`phonon_IDs`) and the S3 reads are replaced, so these test
the choice of method, the fall-through and the messages.
"""

import logging

import pytest
from emmet.core.band_theory import BSPathType

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.routes.materials.phonon import PhononRester

PHEASY_ONLY = {"pheasy": ["aaahikjt"]}
DFPT_ONLY = {"dfpt": ["aaaaadfo"]}
BOTH = {"dfpt": ["aaaaaaft"], "pheasy": ["aaaeguxu"]}


class Calls:
    """What the fake S3 reads were asked for, and what they hold."""

    def __init__(self):
        self.fetched: list[tuple[str, str, str]] = []  # (kind, phonon id, method)
        self.missing: set[tuple[str, str, str]] = set()  # reads that find no row


@pytest.fixture
def make(monkeypatch):
    """Build a `PhononRester` for a material with the given `phonon_IDs`."""

    def build(phonon_ids, *, missing=()):
        calls = Calls()
        calls.missing = set(missing)

        rester = PhononRester(api_key="a" * 32, use_document_model=False)

        class FakeSummary:
            @staticmethod
            def search(material_ids, fields):
                return [{"material_id": material_ids, "phonon_IDs": phonon_ids}]

        monkeypatch.setattr(PhononRester, "summary_rester", FakeSummary())

        def fetch(kind):
            def fake(identifier, phonon_method, *args):
                calls.fetched.append((kind, identifier, phonon_method))
                if (kind, identifier, phonon_method) in calls.missing:
                    return None
                return {"kind": kind, "id": identifier, "method": phonon_method}

            return fake

        monkeypatch.setattr(rester, "_fetch_bandstructure", fetch("bs"))
        monkeypatch.setattr(rester, "_fetch_dos", fetch("dos"))
        monkeypatch.setattr(rester, "_fetch_forceconstants", fetch("fc"))
        return rester, calls

    return build


# --- choosing the method ---------------------------------------------------------


@pytest.mark.parametrize(
    "phonon_ids, method",
    [(PHEASY_ONLY, "pheasy"), (DFPT_ONLY, "dfpt"), (BOTH, "pheasy")],
)
def test_default_method_follows_the_data(make, phonon_ids, method):
    rester, calls = make(phonon_ids)
    assert rester.get_dos_from_material_id("mp-x")["method"] == method
    assert rester.get_bandstructure_from_material_id("mp-x")["method"] == method
    assert {m for *_, m in calls.fetched} == {method}


def test_explicit_method_is_honoured(make):
    rester, _ = make(BOTH)
    assert rester.get_dos_from_material_id("mp-x", "dfpt")["method"] == "dfpt"
    assert rester.get_dos_from_material_id("mp-x", "pheasy")["method"] == "pheasy"


def test_method_can_still_be_passed_positionally(make):
    rester, _ = make(BOTH)
    assert rester.get_dos_from_material_id("mp-x", "dfpt")["id"] == "aaaaaaft"
    assert rester.get_bandstructure_from_material_id("mp-x", "dfpt")["method"] == "dfpt"


def test_choice_is_logged_at_debug(make, caplog):
    rester, _ = make(BOTH)
    with caplog.at_level(logging.DEBUG, logger="mp_api.client"):
        rester.get_dos_from_material_id("mp-x")
    record = next(r for r in caplog.records if "Using pheasy" in r.getMessage())
    assert record.levelno == logging.DEBUG
    assert "available: dfpt, pheasy" in record.getMessage()


# --- explicit methods never fall through -----------------------------------------


def test_explicit_method_missing_names_what_is_available(make):
    rester, calls = make(PHEASY_ONLY)
    with pytest.raises(MPRestError) as excinfo:
        rester.get_bandstructure_from_material_id("mp-x", "dfpt")
    message = str(excinfo.value)
    assert "No dfpt phonon data for mp-x" in message
    assert "available: pheasy" in message
    assert 'phonon_method="pheasy"' in message
    assert calls.fetched == []


def test_explicit_method_does_not_fall_through_on_a_missing_row(make):
    rester, calls = make(BOTH, missing={("dos", "aaaeguxu", "pheasy")})
    with pytest.raises(MPRestError, match="No phonon DOS found for mp-x"):
        rester.get_dos_from_material_id("mp-x", "pheasy")
    assert [m for *_, m in calls.fetched] == ["pheasy"]


# --- falling through to another method (default method only) ---------------------


def test_missing_row_falls_through_with_a_warning(make, caplog):
    rester, calls = make(BOTH, missing={("bs", "aaaeguxu", "pheasy")})
    with caplog.at_level(logging.INFO, logger="mp_api.client"):
        bs = rester.get_bandstructure_from_material_id("mp-x")
    assert bs["method"] == "dfpt"
    assert [m for *_, m in calls.fetched] == ["pheasy", "dfpt"]

    record = next(r for r in caplog.records if "using dfpt" in r.getMessage())
    assert record.levelno == logging.WARNING
    assert "No pheasy phonon band structure for mp-x (aaaeguxu)" in record.getMessage()
    assert "aaaaaaft" in record.getMessage()


def test_no_warning_without_a_fall_through(make, caplog):
    rester, _ = make(BOTH)
    with caplog.at_level(logging.INFO, logger="mp_api.client"):
        rester.get_dos_from_material_id("mp-x")
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_all_candidates_missing_lists_what_was_tried(make):
    rester, _ = make(
        BOTH, missing={("dos", "aaaeguxu", "pheasy"), ("dos", "aaaaaaft", "dfpt")}
    )
    with pytest.raises(MPRestError) as excinfo:
        rester.get_dos_from_material_id("mp-x")
    assert "tried pheasy aaaeguxu, dfpt aaaaaaft" in str(excinfo.value)


# --- path types ------------------------------------------------------------------


@pytest.mark.parametrize("path_type", ["hinuma", BSPathType.latimer_munro])
def test_dfpt_has_only_one_path_type(make, path_type):
    rester, calls = make(DFPT_ONLY)
    with pytest.raises(MPRestError, match="only available with path_type"):
        rester.get_bandstructure_from_material_id("mp-x", path_type=path_type)
    assert calls.fetched == []


def test_explicit_dfpt_with_other_path_type_fails_before_any_lookup(make):
    rester, calls = make(BOTH)
    with pytest.raises(MPRestError, match="setyawan_curtarolo"):
        rester.get_bandstructure_from_material_id(
            "mp-x", "dfpt", path_type=BSPathType.hinuma
        )
    assert calls.fetched == []


def test_default_method_skips_dfpt_for_other_path_types(make):
    rester, calls = make(BOTH, missing={("bs", "aaaeguxu", "pheasy")})
    with pytest.raises(MPRestError, match="No phonon band structure found"):
        rester.get_bandstructure_from_material_id("mp-x", path_type="hinuma")
    # never silently a different k-path
    assert [m for *_, m in calls.fetched] == ["pheasy"]


def test_default_method_uses_pheasy_for_other_path_types(make):
    rester, _ = make(BOTH)
    bs = rester.get_bandstructure_from_material_id("mp-x", path_type="hinuma")
    assert bs["method"] == "pheasy"


def test_path_type_is_not_a_constraint_on_the_dos(make):
    rester, _ = make(DFPT_ONLY)
    assert rester.get_dos_from_material_id("mp-x")["method"] == "dfpt"


# --- materials without usable data -----------------------------------------------


@pytest.mark.parametrize("phonon_ids", [None, {}, {"dfpt": [], "pheasy": []}])
def test_material_without_phonon_data(make, phonon_ids):
    """Used to raise TypeError for `None`."""
    rester, calls = make(phonon_ids)
    with pytest.raises(MPRestError, match="No phonon data found for material ID mp-x"):
        rester.get_dos_from_material_id("mp-x")
    with pytest.raises(MPRestError, match="No phonon data found for material ID mp-x"):
        rester.get_bandstructure_from_material_id("mp-x", "pheasy")
    assert calls.fetched == []


def test_unknown_material(monkeypatch):
    rester = PhononRester(api_key="a" * 32, use_document_model=False)

    class Empty:
        @staticmethod
        def search(material_ids, fields):
            return []

    monkeypatch.setattr(PhononRester, "summary_rester", Empty())
    with pytest.raises(MPRestError, match="No phonon data found for material ID mp-0"):
        rester.get_dos_from_material_id("mp-0")


# --- force constants -------------------------------------------------------------


def test_force_constants_from_dfpt_fail_before_any_lookup(make):
    rester, calls = make(BOTH)
    with pytest.raises(MPRestError) as excinfo:
        rester.get_forceconstants_from_material_id("mp-x", "dfpt")
    assert "no force constants" in str(excinfo.value)
    assert 'phonon_method="pheasy"' in str(excinfo.value)
    assert calls.fetched == []


def test_force_constants_come_from_pheasy(make):
    rester, _ = make(BOTH)
    assert rester.get_forceconstants_from_material_id("mp-x", "pheasy")["id"] == (
        "aaaeguxu"
    )


def test_force_constants_of_a_dfpt_only_material(make):
    rester, _ = make(DFPT_ONLY)
    with pytest.raises(MPRestError, match="No pheasy phonon data for mp-x"):
        rester.get_forceconstants_from_material_id("mp-x", "pheasy")


# --- thermo quantities -----------------------------------------------------------


def test_thermo_quantities_resolve_the_method(make, monkeypatch):
    rester, calls = make(PHEASY_ONLY)
    seen = {}

    def fake_search(identifiers, phonon_method):
        seen.update(identifiers=identifiers, phonon_method=phonon_method)
        return [{"identifier": identifiers}]

    class FakeDoc:
        def __init__(self, **kwargs):
            seen["doc"] = kwargs

        def compute_thermo_quantities(self, temps):
            return {"temps": temps}

    monkeypatch.setattr(rester, "search", fake_search)
    monkeypatch.setattr("mp_api.client.routes.materials.phonon.PhononBSDOSDoc", FakeDoc)

    assert len(rester.compute_thermo_quantities(material_id="mp-x")["temps"]) == 100
    assert seen["identifiers"] == "aaahikjt"
    assert seen["phonon_method"] == "pheasy"
    assert rester.use_document_model is False  # restored


def test_thermo_quantities_need_a_method_with_an_identifier(make):
    rester, _ = make(BOTH)
    with pytest.raises(MPRestError, match="Could not resolve"):
        rester.compute_thermo_quantities(identifier="aaaeguxu")


# --- MPRester shortcuts ----------------------------------------------------------


@pytest.fixture
def mpr(monkeypatch):
    from mp_api.client import MPRester
    from mp_api.client.core.client import _Rester

    monkeypatch.setattr(
        _Rester, "_get_heartbeat_info", staticmethod(lambda ep: ("2026.04.13", []))
    )
    monkeypatch.setattr(MPRester, "get_emmet_version", staticmethod(lambda ep: None))
    return MPRester(api_key="a" * 32)


def test_mprester_shortcuts_pass_everything_through(mpr, monkeypatch):
    seen = {}

    def bs(self, material_id, phonon_method=None, path_type=None):
        seen["bs"] = (material_id, phonon_method, path_type)
        return "bs"

    def dos(self, material_id, phonon_method=None):
        seen["dos"] = (material_id, phonon_method)
        return "dos"

    monkeypatch.setattr(PhononRester, "get_bandstructure_from_material_id", bs)
    monkeypatch.setattr(PhononRester, "get_dos_from_material_id", dos)

    assert mpr.get_phonon_bandstructure_by_material_id("mp-x") == "bs"
    assert seen["bs"] == ("mp-x", None, BSPathType.setyawan_curtarolo)
    mpr.get_phonon_bandstructure_by_material_id("mp-x", "dfpt", "hinuma")
    assert seen["bs"] == ("mp-x", "dfpt", "hinuma")

    assert mpr.get_phonon_dos_by_material_id("mp-x") == "dos"
    assert seen["dos"] == ("mp-x", None)
    mpr.get_phonon_dos_by_material_id("mp-x", phonon_method="pheasy")
    assert seen["dos"] == ("mp-x", "pheasy")
