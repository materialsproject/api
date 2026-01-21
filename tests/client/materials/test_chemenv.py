import os
from ..conftest import client_search_testing, requires_api_key

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

sub_doc_fields: list = []

alt_name_dict: dict = {
    "material_ids": "material_id",
    "exclude_elements": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}

custom_field_tests: dict = {
    "material_ids": ["mp-22526"],
    "elements": ["Si", "O"],
    "exclude_elements": ["Si", "O"],
    "chemenv_symbol": ["S:1"],
    "chemenv_iupac": ["IC-12"],
    "chemenv_iucr": ["[2l]"],
    "chemenv_name": ["Octahedron"],
    "species": ["Cu2+"],
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
