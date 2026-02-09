import os
from ..conftest import client_search_testing, requires_api_key

import pytest

from mp_api.client.routes.materials.elasticity import ElasticityRester


@pytest.fixture
def rester():
    rester = ElasticityRester()
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

alt_name_dict: dict = {
    "material_ids": "material_id",
    "elastic_anisotropy": "universal_anisotropy",
    "poisson_ratio": "homogeneous_poisson",
    "g_voigt": "bulk_modulus",
    "g_reuss": "bulk_modulus",
    "g_vrh": "bulk_modulus",
    "k_voigt": "shear_modulus",
    "k_reuss": "shear_modulus",
    "k_vrh": "shear_modulus",
}

custom_field_tests: dict = {"material_ids": ["mp-149"]}


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
