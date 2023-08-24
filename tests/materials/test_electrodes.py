import os
from core_function import client_search_testing

import pytest
from pymatgen.core.periodic_table import Element

from mp_api.client.routes.materials.electrodes import ElectrodeRester


@pytest.fixture
def rester():
    rester = ElectrodeRester()
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
    "battery_ids": "battery_id",
    "formula": "battery_id",
    "exclude_elements": "battery_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-22526"],
    "battery_ids": ["mp-22526_Li"],
    "working_ion": Element("Li"),
    "formula": "CoO2",
    "chemsys": "Co-O",
    "elements": ["Co", "O"],
    "exclude_elements": ["Co"],
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
