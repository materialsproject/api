import os

import pytest

from mp_api.client.routes.materials import DOIRester

from core_function import client_search_testing


@pytest.mark.skipif(os.getenv("MP_API_KEY") is None, reason="No API key found.")
def test_doi_search():
    client_search_testing(
        search_method=DOIRester().search,
        excluded_params=[
            "num_chunks",
            "chunk_size",
            "all_fields",
            "fields",
        ],
        alt_name_dict={
            "material_ids": "material_id",
        },
        custom_field_tests={
            "material_ids": ["mp-149", "mp-13"],
            "material_ids": "mp-149",
        },
        sub_doc_fields=[],
    )
