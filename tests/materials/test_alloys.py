import os

import pytest

from mp_api.client.routes.materials.alloys import AlloysRester

from ..conftest import client_search_testing, requires_api_key


@requires_api_key
def test_alloys_search():
    client_search_testing(
        search_method=AlloysRester().search,
        excluded_params=[
            "num_chunks",
            "chunk_size",
            "all_fields",
            "fields",
        ],
        alt_name_dict={
            "material_ids": "pair_id",
            "formulae": "alloy_pair",
        },
        custom_field_tests={
            "material_ids": ["mp-70", "mp-1014212"],
            "material_ids": "mp-1014212",
            "formulae": ["Rb", "Si"],
        },
        sub_doc_fields=[],
    )
