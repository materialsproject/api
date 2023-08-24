import os
from core_function import client_search_testing

import pytest
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from pymatgen.analysis.magnetism import Ordering

from mp_api.client.routes.materials.summary import SummaryRester

excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "equilibrium_reaction_energy",  # temp until data update
    "total_energy",  # temp until data update
    "exclude_elements",  # temp until data update
    "num_elements",  # temp until server timeout increase
    "num_sites",  # temp until server timeout increase
    "density",  # temp until server timeout increase
    "total_magnetization",  # temp until server timeout increase
]

alt_name_dict = {
    "material_ids": "material_id",
    "formula": "formula_pretty",
    "exclude_elements": "formula_pretty",
    "piezoelectric_modulus": "e_ij_max",
    "crystal_system": "symmetry",
    "spacegroup_symbol": "symmetry",
    "spacegroup_number": "symmetry",
    "total_energy": "energy_per_atom",
    "formation_energy": "formation_energy_per_atom",
    "uncorrected_energy": "uncorrected_energy_per_atom",
    "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
    "magnetic_ordering": "ordering",
    "elastic_anisotropy": "universal_anisotropy",
    "poisson_ratio": "homogeneous_poisson",
    "num_sites": "nsites",
    "num_elements": "nelements",
    "surface_energy_anisotropy": "surface_anisotropy",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "formula": "SiO2",
    "chemsys": "Si-O",
    "elements": ["Si", "O"],
    "possible_species": ["O2-"],
    "crystal_system": CrystalSystem.cubic,
    "spacegroup_number": 38,
    "spacegroup_symbol": "Amm2",
    "has_props": [HasProps.dielectric],
    "theoretical": True,
    "has_reconstructed": False,
    "magnetic_ordering": Ordering.FM,
}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client():
    search_method = SummaryRester().search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=[],
    )
