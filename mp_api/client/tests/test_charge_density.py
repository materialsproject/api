import os
import pytest
from emmet.core.charge_density import ChgcarDataDoc
from mp_api.client.routes.charge_density import ChargeDensityRester

import typing


@pytest.fixture
def rester():
    rester = ChargeDensityRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "return",
]

sub_doc_fields = []  # type: list

alt_name_dict = {}  # type: dict

custom_field_tests = {}  # type: dict


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
                    }
                elif param_type == typing.Tuple[float, float]:
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


def test_download_for_task_ids(tmpdir, rester):

    n = rester.download_for_task_ids(
        task_ids=["mp-655585", "mp-1057373", "mp-1059589", "mp-1440634", "mp-1791788"],
        path=tmpdir,
    )
    files = [f for f in os.listdir(tmpdir)]

    assert "mp-1791788.json.gz" in files


def test_extract_s3_url_info(rester):

    url_doc_dict = {
        "task_id": "mp-1896591",
        "url": "https://minio.materialsproject.org/phuck/atomate_chgcar_fs/6021584c12afbe14911d1b8e",
        "s3_url_prefix": "https://mp-volumetric.s3.amazonaws.com/atomate_chgcar_fs/",
        "fs_id": "6021584c12afbe14911d1b8e",
        "requested_datetime": {"$date": {"$numberLong": "1650389943209"}},
        "expiry_datetime": None,
    }

    url_doc = ChgcarDataDoc(**url_doc_dict)

    bucket, prefix = rester._extract_s3_url_info(url_doc)

    assert bucket == "phuck"
    assert prefix == "atomate_chgcar_fs"

    bucket, prefix = rester._extract_s3_url_info(url_doc, use_minio=False)

    assert bucket == "mp-volumetric"
    assert prefix == "atomate_chgcar_fs"
