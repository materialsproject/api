import os
from core_function import client_search_testing

import pytest

from mp_api.client.routes.materials.tasks import TaskRester


@pytest.fixture
def rester():
    rester = TaskRester(monty_decode=False)
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "formula",
    "elements",
    "exclude_elements",
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "formula": "task_id",
    "task_ids": "task_id",
    "exclude_elements": "task_id",
}  # type: dict

custom_field_tests = {
    "chemsys": "Si-O",
    "task_ids": ["mp-149"],
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


def test_get_trajectories(rester):
    trajectories = [traj for traj in rester.get_trajectory("mp-149")]

    for traj in trajectories:
        assert ("@module", "pymatgen.core.trajectory") in traj.items()
