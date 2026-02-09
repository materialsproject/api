import os

import pytest
from emmet.core.mpid import MPID, AlphaID
from emmet.core.trajectory import RelaxTrajectory
from emmet.core.utils import utcnow

from mp_api.client.routes.materials.tasks import TaskRester

from ..conftest import client_search_testing, requires_api_key


@pytest.fixture
def rester():
    rester = TaskRester()
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

sub_doc_fields: list = []

alt_name_dict: dict = {
    "formula": "task_id",
    "task_ids": "task_id",
    "exclude_elements": "task_id",
}

custom_field_tests: dict = {
    "chemsys": "Si-O",
    "last_updated": (None, utcnow()),
    "task_ids": ["mp-149"],
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


@pytest.mark.parametrize("mpid", ["mp-149", MPID("mp-149"), AlphaID("mp-149")])
def test_get_trajectories(rester, mpid):
    trajectory = rester.get_trajectory(mpid)

    expected_model_fields = {
        field_name
        for field_name, field in RelaxTrajectory.model_fields.items()
        if not field.exclude
    }
    assert set(trajectory) == expected_model_fields
