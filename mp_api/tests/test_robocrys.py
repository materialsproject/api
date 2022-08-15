import os
import pytest
from mp_api.client.routes.robocrys import RobocrysRester

from pymatgen.core.periodic_table import Element


@pytest.fixture
def rester():
    rester = RobocrysRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client(rester):
    search_method = rester.search

    if search_method is not None:

        q = {"keywords": ["silicon"], "num_chunks": 1}

        doc = search_method(**q)[0]

        assert doc.description is not None
        assert doc.condensed_structure is not None
