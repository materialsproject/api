import os
from core_function import client_search_testing

import pytest
from emmet.core.grain_boundary import GBTypeEnum

from mp_api.client.routes.materials.grain_boundary import GrainBoundaryRester


@pytest.fixture
def rester():
    rester = GrainBoundaryRester()
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

alt_name_dict = {"material_ids": "task_id", "separation_energy": "w_sep"}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-81"],
    "gb_plane": ["1", "0", "0"],
    "rotation_axis": ["1", "0", "0"],
    "sigma": 5,
    "type": GBTypeEnum.twist,
    "chemsys": "Mo",
    "pretty_formula": "Mo",
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
