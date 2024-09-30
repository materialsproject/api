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
    "g_reuss": "bulk_modulus",
    "g_vrh": "bulk_modulus",
    "g_voigt": "bulk_modulus",
    "k_reuss": "shear_modulus",
    "k_vrh": "shear_modulus",
    "k_voigt": "shear_modulus",
    "num_sites": "nsites",
    "num_elements": "nelements",
    "surface_energy_anisotropy": "surface_anisotropy",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "formula": "SiO2",
    "chemsys": "Si-O",
    "elements": ["Si", "O"],
    "exclude_elements": ["Si", "O"],
    "possible_species": ["O2-"],
    "crystal_system": CrystalSystem.cubic,
    "spacegroup_number": 38,
    "spacegroup_symbol": "Amm2",
    "has_props": [HasProps.dielectric],
    "theoretical": True,
    "has_reconstructed": False,
    "magnetic_ordering": Ordering.FM,
}  # type: dict


@pytest.mark.skipif(os.getenv("MP_API_KEY") is None, reason="No API key found.")
def test_client():
    search_method = SummaryRester().search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=[],
    )
