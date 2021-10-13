import os
import pytest
from mp_api.routes.charge_density.client import ChargeDensityRester

import inspect
import typing

resters = [ChargeDensityRester()]

excluded_params = [
    "sort_field",
    "ascending",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields = []  # type: list

alt_name_dict = {}  # type: dict

custom_field_tests = {}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.parametrize("rester", resters)
def test_client(rester):
    # Get specific search method
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and bollean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in excluded_params:
                param_type = entry[1].__args__[0]
                q = None
                if param_type is typing.Tuple[int, int]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is typing.Tuple[float, float]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (0, 100.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is bool:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param in custom_field_tests:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }

                doc = search_method(**q)[0].dict()
                for sub_field in sub_doc_fields:
                    if sub_field in doc:
                        doc = doc[sub_field]

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )


@pytest.mark.xfail  # temp until new deployment
def test_download_for_task_ids(tmpdir):
    rester = resters[0]

    n = rester.download_for_task_ids(
        task_ids=["mp-655585", "mp-1057373", "mp-1059589", "mp-1440634", "mp-1791788"],
        path=tmpdir,
    )
    files = [f for f in os.listdir(tmpdir)]

    assert "mp-1791788.json.gz" in files
