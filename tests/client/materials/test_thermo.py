import os

import pytest
from emmet.core.types.enums import ThermoType
from pymatgen.analysis.phase_diagram import PhaseDiagram

from mp_api._test_utils import client_search_testing, requires_api_key
from mp_api.client.routes.materials.thermo import ThermoRester


@pytest.fixture
def rester():
    rester = ThermoRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "equilibrium_reaction_energy",
]

sub_doc_fields: list = []

alt_name_dict: dict = {
    "formula": "formula_pretty",
    "material_ids": "material_id",
    "thermo_ids": "material_id",
    "thermo_types": "thermo_type",
    "total_energy": "energy_per_atom",
    "formation_energy": "formation_energy_per_atom",
    "uncorrected_energy": "uncorrected_energy_per_atom",
    "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
    "num_elements": "nelements",
    "num_sites": "nsites",
}

custom_field_tests: dict = {
    "material_ids": ["mp-149"],
    "thermo_ids": ["mp-149_GGA_GGA+U"],
    "thermo_types": [ThermoType.GGA_GGA_U],
    "formula": "SiO2",
    "chemsys": "Si-O",
}


@requires_api_key
def test_client(rester):
    search_method = rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


def test_get_phase_diagram_from_chemsys():
    # Test that a phase diagram is returned

    pd = ThermoRester().get_phase_diagram_from_chemsys("Hf-Pm", thermo_type="GGA_GGA+U")
    assert isinstance(
        pd,
        PhaseDiagram,
    )


@pytest.mark.parametrize("has_access", [False, True])
def test_get_phase_diagram_from_chemsys_gnome_access(monkeypatch, has_access):
    """The (access-controlled, BY-NC licensed) GNoMe entries of the pre-built phase
    diagrams are only served to API keys with access to the GNoMe data."""
    chemsys = "Cu-Se-Si"  # has a GNoMe ground state (Cu3SiSe4) as of v2026.09.28
    monkeypatch.setattr(
        ThermoRester, "_has_gnome_access", lambda self, timeout=None: True
    )
    full = ThermoRester().get_phase_diagram_from_chemsys(chemsys)
    gnome = {str(e.entry_id) for e in full.all_entries if e.data["license"] == "BY-NC"}
    if not gnome:
        pytest.skip(f"No GNoMe entries in the served {chemsys} phase diagram")

    monkeypatch.setattr(
        ThermoRester, "_has_gnome_access", lambda self, timeout=None: has_access
    )
    pd = ThermoRester().get_phase_diagram_from_chemsys(chemsys)
    energies = {str(e.entry_id): e.energy_per_atom for e in pd.all_entries}
    full_energies = {str(e.entry_id): e.energy_per_atom for e in full.all_entries}
    if has_access:
        assert energies == full_energies
        return

    # the other entries keep their energies, except for GGA(+U)-only entries placed onto
    # the r2SCAN hull (which are re-referenced to it without the GNoMe entries, so can
    # only go up), and the hull is rebuilt without the GNoMe entries:
    assert set(energies) == set(full_energies) - gnome
    for entry in pd.all_entries:
        i = str(entry.entry_id)
        if any("without GNoMe" in adj.name for adj in entry.energy_adjustments):
            assert energies[i] > full_energies[i]
        else:
            assert energies[i] == pytest.approx(full_energies[i])
    rebuilt = PhaseDiagram(list(pd.all_entries))
    assert {str(e.entry_id) for e in pd.stable_entries} == {
        str(e.entry_id) for e in rebuilt.stable_entries
    }
