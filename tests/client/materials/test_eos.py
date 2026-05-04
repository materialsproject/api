import os

import pytest

from mp_api._test_utils import client_search_testing, requires_api_key

from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.client.routes.materials.eos import EOSRester


@pytest.fixture
def rester():
    rester = EOSRester()
    yield rester
    rester.session.close()


excluded_params = [
    "energies",
    "volumes",
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields: list = []

alt_name_dict: dict = {"task_ids": "task_id"}

custom_field_tests: dict = {"task_ids": ["mp-149"]}


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


@requires_api_key
def test_warnings_errors(rester):

    with pytest.warns(
        MPRestWarning, match="`material_id` has been replaced by `task_id`"
    ):
        rester.search(material_ids=["mp-149"], num_chunks=1, chunk_size=1)

    with pytest.raises(MPRestError, match="You have specified both"):
        rester.search(material_ids=["mp-149"], task_ids=["mp-1"])
