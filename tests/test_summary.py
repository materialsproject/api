from emmet.core.symmetry import CrystalSystem
from emmet.core.summary import HasProps
from pymatgen.analysis.magnetism import Ordering
from mp_api.client.routes.summary import SummaryRester
import os
import pytest

import typing

excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "equilibrium_reaction_energy",  # temp until data update
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
    "piezoelectric_modulus": "e_ij_max",
    "surface_energy_anisotropy": "surface_anisotropy",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "formula": "SiO2",
    "chemsys": "Si-O",
    "elements": ["Si", "O"],
    "exclude_elements": ["Si"],
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

    # Get list of parameters
    param_tuples = list(typing.get_type_hints(search_method).items())

    # Query API for each numeric and boolean parameter and check if returned
    for entry in param_tuples:
        param = entry[0]
        if param not in excluded_params:
            param_type = entry[1].__args__[0]
            q = None

            if param in custom_field_tests:
                project_field = alt_name_dict.get(param, None)
                q = {
                    param: custom_field_tests[param],
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type == typing.Tuple[int, int]:
                project_field = alt_name_dict.get(param, None)
                q = {
                    param: (-100, 100),
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type == typing.Tuple[float, float]:
                project_field = alt_name_dict.get(param, None)
                q = {
                    param: (-100.12, 100.12),
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type is bool:
                project_field = alt_name_dict.get(param, None)
                q = {
                    param: False,
                    "chunk_size": 1,
                    "num_chunks": 1,
                }

            docs = search_method(**q)

            if len(docs) > 0:
                doc = docs[0].dict()
            else:
                raise ValueError("No documents returned")

            assert (
                doc[project_field if project_field is not None else param] is not None
            )
