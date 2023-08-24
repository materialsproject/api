import os
from core_function import client_search_testing

import pytest
from pymatgen.core.periodic_table import Element

from mp_api.client.routes.molecules.jcesr import JcesrMoleculesRester


@pytest.fixture
def rester():
    rester = JcesrMoleculesRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "charge",
]

sub_doc_fields = []  # type: list

alt_name_dict = {}  # type: dict

custom_field_tests = {
    "elements": [Element("H")],
    "pointgroup": "C1",
    "smiles": "C#CC(=C)C.CNCCNC",
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
