import os
from ..conftest import client_search_testing, requires_api_key

import pytest
from emmet.core.types.enums import ThermoType
from pymatgen.analysis.phase_diagram import PhaseDiagram

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
    "thermo_ids": "thermo_id",
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

    assert isinstance(
        ThermoRester().get_phase_diagram_from_chemsys("Hf-Pm", thermo_type="GGA_GGA+U"),
        PhaseDiagram,
    )
