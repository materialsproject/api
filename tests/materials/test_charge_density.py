import os

import pytest
from core_function import client_search_testing

from mp_api.client.routes.materials.charge_density import ChargeDensityRester


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

alt_name_dict = {
    "task_ids": "task_id",
}  # type: dict

custom_field_tests = {"task_ids": ["mp-1985345", "mp-1896118"]}  # type: dict


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


def test_download_for_task_ids(tmpdir, rester):
    rester.download_for_task_ids(
        task_ids=["mp-655585", "mp-1057373", "mp-1059589", "mp-1440634", "mp-1791788"],
        path=tmpdir,
    )
    files = [f for f in os.listdir(tmpdir)]

    assert "mp-1791788.json.gz" in files
