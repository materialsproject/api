import os
from .core_function import client_search_testing

import pytest
from pymatgen.core.periodic_table import Element

from mp_api.client.routes.molecules.jcesr import JcesrMoleculesRester

from ..conftest import requires_api_key


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

sub_doc_fields: list = []

alt_name_dict: dict = {"task_ids": "task_id"}

custom_field_tests: dict = {
    "task_ids": ["mol-45228"],
    "elements": [Element("H")],
    "pointgroup": "C1",
    "smiles": "C#CC(=C)C.CNCCNC",
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


def test_warning():
    with pytest.warns(UserWarning, match="unmaintained legacy molecules"):
        JcesrMoleculesRester()
