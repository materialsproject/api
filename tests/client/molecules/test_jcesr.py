import os
from mp_api._test_utils import (
    client_search_testing,
    client_pagination,
    client_sort,
    requires_api_key,
)

import pytest
from pymatgen.core.periodic_table import Element

from mp_api.client.core.exceptions import MPRestWarning
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
    "_page",
    "_sort_fields",
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
        float_bounds=(-3000.12, 3000.12),
    )


def test_warning():
    with pytest.warns(MPRestWarning, match="unmaintained legacy molecules"):
        JcesrMoleculesRester()


@requires_api_key
def test_pagination():
    with JcesrMoleculesRester() as rester:
        client_pagination(rester.search, "task_id")


@pytest.mark.xfail(reason="Sort requires API redeployment", strict=False)
@requires_api_key
@pytest.mark.parametrize("sort_field", ["task_id", "IE", "EA"])
def test_sort(sort_field):
    with JcesrMoleculesRester() as rester:
        client_sort(rester.search, sort_field)
