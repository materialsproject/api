import os
from core_function import client_search_testing

import pytest
from emmet.core.xas import Edge, Type
from pymatgen.core.periodic_table import Element

from mp_api.client.routes.materials.xas import XASRester


@pytest.fixture
def rester():
    rester = XASRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "material_ids",
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "required_elements": "elements",
    "formula": "formula_pretty",
    "exclude_elements": "material_id",
}  # type: dict

custom_field_tests = {
    "edge": Edge.L2_3,
    "spectrum_type": Type.EXAFS,
    "absorbing_element": Element("Ce"),
    "required_elements": [Element("Ce")],
    "formula": "Ce(WO4)2",
    "chemsys": "Ce-O-W",
    "elements": ["Ce"],
}  # type: dict


@pytest.mark.skip(reason="Temp skip until timeout update.")
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
