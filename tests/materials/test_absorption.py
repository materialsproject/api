import os

import pytest

from emmet.core.phonon import PhononBS, PhononDOS

from mp_api.client.core import MPRestError
from mp_api.client.routes.materials.absorption import AbsorptionRester

from core_function import client_search_testing

@pytest.mark.skipif(os.getenv("MP_API_KEY") is None, reason="No API key found.")
def test_absorption_search():

    client_search_testing(
        search_method=AbsorptionRester().search,
        excluded_params=[
            "num_chunks",
            "chunk_size",
            "all_fields",
            "fields",
        ],
        alt_name_dict={
            "material_ids": "material_id",
            "num_sites": "nsites",
            "num_elements": "nelements",
            "band_gap": "bandgap",
        },
        custom_field_tests={
            "material_ids": ["mp-149", "mp-239"],
            "material_ids": "mp-149",
            "num_sites": (6,7),
            "num_sites": 7,
            "num_elements": 5,
            "num_elements": (4,5),
            "volume": (115,116),
            "volume": 115.5,
            "density": (2.9,3),
            "density": 2.933,
            "band_gap": (1,1.05),
            "band_gap": 1.,
        },
        sub_doc_fields=[],
    )