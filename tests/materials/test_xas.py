import os
from core_function import client_search_testing

import pytest

from emmet.core.types.enums import XasEdge, XasType
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
    "spectrum_ids": "spectrum_id"
}  # type: dict

custom_field_tests = {
    "edge": XasEdge.L2,
    "spectrum_type": XasType.EXAFS,
    "absorbing_element": Element("Ce"),
    "required_elements": [Element("Ce")],
    "formula": "Ce(WO4)2",
    "chemsys": "Ce-O-W",
    "elements": ["Ce"],
    "spectrum_ids": ["mp-1194531-XANES-Fe-L2","mp-1194531-XANES-Fe-K"],
}  # type: dict


@pytest.mark.skipif(os.getenv("MP_API_KEY") is None, reason="No API key found.")
def test_client(rester):
    search_method = rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )
