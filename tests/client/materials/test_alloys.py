import os

import pytest

try:
    import pymatgen.analysis.alloys
except ImportError:
    pytest.skip(
        "Please `pip install pymatgen-analysis-alloys` to use the `materials.alloys` endpoint",
        allow_module_level=True,
    )

from mp_api.client.routes.materials.alloys import AlloysRester

from ..conftest import client_search_testing, requires_api_key


@requires_api_key
def test_alloys_search():
    with AlloysRester() as rester:
        client_search_testing(
            search_method=rester.search,
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
