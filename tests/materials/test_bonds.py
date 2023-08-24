import os
from core_function import client_search_testing
import pytest
from mp_api.client.routes.materials.bonds import BondsRester


@pytest.fixture
def rester():
    rester = BondsRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "material_ids": "material_id",
    "max_bond_length": "bond_length_stats",
    "min_bond_length": "bond_length_stats",
    "mean_bond_length": "bond_length_stats",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "coordination_envs": ["Mo-S(6)"],
    "coordination_envs_anonymous": ["A-B(6)"],
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
