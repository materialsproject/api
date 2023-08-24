import os
from core_function import client_search_testing

import pytest

from mp_api.client.routes.materials.chemenv import ChemenvRester


@pytest.fixture
def rester():
    rester = ChemenvRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "volume",
    "csm",  # temp until timeout fix
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "material_ids": "material_id",
    "exclude_elements": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-22526"],
    "elements": ["Si", "O"],
    "exclude_elements": ["Si", "O"],
    "chemenv_symbol": ["S:1"],
    "chemenv_iupac": ["IC-12"],
    "chemenv_iucr": ["[2l]"],
    "chemenv_name": ["Octahedron"],
    "species": ["Cu2+"],
}  # type: dict


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_client(rester):
    search_method = rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )
