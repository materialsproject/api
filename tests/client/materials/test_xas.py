from typing import Any

import pytest
from emmet.core.types.enums import XasEdge, XasType
from pymatgen.core.periodic_table import Element

from mp_api._test_utils import (
    client_pagination,
    client_search_testing,
    client_sort,
    requires_api_key,
)
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

sub_doc_fields: list[str] = []

alt_name_dict: dict[str, str] = {
    "required_elements": "elements",
    "formula": "formula_pretty",
    "exclude_elements": "absorbing_element",
    "spectrum_ids": "absorbing_element",
}

custom_field_tests: dict[str, Any] = {
    "edge": XasEdge.L2,
    "spectrum_type": XasType.EXAFS,
    "absorbing_element": Element("Ce"),
    "required_elements": [Element("Ce")],
    "formula": "Ce(WO4)2",
    "chemsys": "Ce-O-W",
    "elements": ["Ce"],
}


@requires_api_key
@pytest.mark.xfail(
    reason="XAS endpoint often too slow to respond.",
    strict=False,
)
def test_client(rester):
    client_search_testing(
        search_method=rester.search,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


# TODO: how to test pagination now that spectrum_id is computed, not stored?
@requires_api_key
def test_pagination():
    with XASRester() as rester:
        client_pagination(
            rester.search, "task_id", additional_fields=["spectrum_type", "edge"]
        )


@pytest.mark.xfail(reason="Sort requires API redeployment", strict=False)
@requires_api_key
@pytest.mark.parametrize(
    "sort_field", ["spectrum_type", "absorbing_element", "chemsys"]
)
def test_sort(sort_field):
    with XASRester() as rester:
        client_sort(rester.search, sort_field)
