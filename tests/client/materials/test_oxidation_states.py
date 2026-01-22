import os
from ..conftest import client_search_testing, requires_api_key

import pytest

from mp_api.client.routes.materials.oxidation_states import OxidationStatesRester


@pytest.fixture
def rester():
    rester = OxidationStatesRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields: list = []

alt_name_dict: dict = {"formula": "material_id", "material_ids": "material_id"}

custom_field_tests: dict = {
    "material_ids": ["mp-149"],
    "formula": "Si",
    "chemsys": "Si-O",
    "possible_species": ["Cr2+", "O2-"],
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
