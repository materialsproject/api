import os
from core_function import client_search_testing

import pytest
from emmet.core.symmetry import CrystalSystem

from mp_api.client.routes.materials.materials import MaterialsRester


@pytest.fixture
def rester():
    rester = MaterialsRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "exclude_elements",  # temp until server timeout increase
    "num_elements",  # temp until server timeout increase
    "num_sites",  # temp until server timeout increase
    "density",  # temp until server timeout increase
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "material_ids": "material_id",
    "formula": "material_id",
    "crystal_system": "symmetry",
    "spacegroup_number": "symmetry",
    "spacegroup_symbol": "symmetry",
    "exclude_elements": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "formula": "Si",
    "chemsys": "Si-P",
    "elements": ["Si", "P"],
    "task_ids": ["mp-149"],
    "crystal_system": CrystalSystem.cubic,
    "spacegroup_number": 38,
    "spacegroup_symbol": "Amm2",
}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client(rester):
    search_method = rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )
