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


def test_get_phase_diagram_from_chemsys_gnome_access(rester):
    """The (access-controlled, BY-NC licensed) GNoMe entries of the pre-built phase
    diagrams are only served to API keys with access to the GNoMe data."""
    rester._gnome_access = True  # (the cached access check)
    full = rester.get_phase_diagram_from_chemsys("Cu-Se-Si")
    rester._gnome_access = False
    pd = rester.get_phase_diagram_from_chemsys("Cu-Se-Si")

    # the GNoMe Cu3SiSe4 is on the r2SCAN-anchored hull (as of v2026.09.28), so the
    # GGA(+U)-only entries placed onto it are re-referenced (up) without it, and the
    # other entries keep their energies:
    gnome = {str(e.entry_id) for e in full.all_entries if e.data["license"] == "BY-NC"}
    full_energies = {str(e.entry_id): e.energy_per_atom for e in full.all_entries}
    energies = {str(e.entry_id): e.energy_per_atom for e in pd.all_entries}
    reref = {
        str(e.entry_id)
        for e in pd.all_entries
        if any("without GNoMe" in adj.name for adj in e.energy_adjustments)
    }
    assert gnome and reref
    assert set(energies) == set(full_energies) - gnome
    for i, energy in energies.items():
        if i in reref:
            assert energy > full_energies[i]
        else:
            assert energy == pytest.approx(full_energies[i])


def test_failed_gnome_access_check_not_cached():
    with ThermoRester(api_key="a" * 32) as rester:  # invalid key, so the check fails
        assert not rester._has_gnome_access()
        assert rester._gnome_access is None  # so checked again on the next call
