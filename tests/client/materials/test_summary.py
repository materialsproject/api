import os
from ..conftest import client_search_testing, requires_api_key

import pytest
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from pymatgen.analysis.magnetism import Ordering

from mp_api.client.routes.materials.summary import SummaryRester
from mp_api.client.core.exceptions import MPRestWarning, MPRestError

excluded_params = [
    "include_gnome",
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

alt_name_dict: dict = {
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
}

custom_field_tests: dict = {
    "material_ids": ["mp-149", "mp-13"],
    "material_ids": "mp-149",
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
    "nelements": (8, 9),
}


@requires_api_key
def test_client():
    search_method = SummaryRester().search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=[],
    )


@requires_api_key
def test_list_like_input():
    search_method = SummaryRester().search

    # These are specifically chosen for the low representation in MP
    # Specifically, these are the four least-represented space groups
    # with at least one member
    sparse_sgn = (93, 101, 172, 179, 211)
    docs_by_number = search_method(
        spacegroup_number=sparse_sgn, fields=["material_id", "symmetry"]
    )
    assert {doc.symmetry.number for doc in docs_by_number} == set(sparse_sgn)

    sparse_symbols = {doc.symmetry.symbol for doc in docs_by_number}
    docs_by_symbol = search_method(
        spacegroup_symbol=sparse_symbols, fields=["material_id", "symmetry"]
    )
    assert {doc.symmetry.symbol for doc in docs_by_symbol} == sparse_symbols
    assert {doc.material_id for doc in docs_by_symbol} == {
        doc.material_id for doc in docs_by_number
    }

    # also chosen for very low document count
    crys_sys = ["Hexagonal", "Cubic"]
    assert {
        doc.symmetry.crystal_system
        for doc in search_method(elements=["Ar"], crystal_system=crys_sys)
    } == set(crys_sys)

    # should fail - we don't support querying by so many list values
    with pytest.raises(ValueError, match="retrieve all data first and then filter"):
        _ = search_method(spacegroup_number=list(range(1, 231)))

    with pytest.raises(ValueError, match="retrieve all data first and then filter"):
        _ = search_method(spacegroup_number=["null" for _ in range(230)])

    with pytest.raises(ValueError, match="retrieve all data first and then filter"):
        _ = search_method(crystal_system=list(CrystalSystem))


@requires_api_key
def test_warning_messages():
    search_method = SummaryRester().search

    with pytest.warns(MPRestWarning, match="You have specified fields used by"):
        _ = search_method(nelements=10)

    with pytest.raises(MPRestError, match="You have specified fields known to both"):
        _ = search_method(nelements=10, num_elements=11)

    with pytest.raises(
        MPRestError,
        match="You have specified the following kwargs which are unknown to",
    ):
        _ = search_method(apples="oranges")

    with pytest.raises(MPRestError, match="not a valid property"):
        _ = search_method(num_elements=10, has_props=["apples"])
