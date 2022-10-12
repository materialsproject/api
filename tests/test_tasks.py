import os
import pytest
from pymatgen.core.trajectory import Trajectory
from mp_api.client.routes.tasks import TaskRester

import typing


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
    "formula", # Timeout issue
]

sub_doc_fields = []  # type: list

alt_name_dict = {"formula": "task_id"}  # type: dict

custom_field_tests = {"chemsys": "Si-O"}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client(rester):
    search_method = rester.search

    if search_method is not None:
        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and boolean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in excluded_params:
                param_type = entry[1].__args__[0]
                q = None

                if param_type == typing.Tuple[int, int]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param_type == typing.Tuple[float, float]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100.12, 100.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param_type is bool:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param in custom_field_tests:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }

                doc = search_method(**q)[0].dict()
                for sub_field in sub_doc_fields:
                    if sub_field in doc:
                        doc = doc[sub_field]

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )


@pytest.mark.xfail(reason="Temporary until redeploy")
def test_get_trajectories(rester):

    trajectories = rester.get_trajectory("mp-149")

    for traj in trajectories:
        assert isinstance(traj, Trajectory)
