import os

import pytest

from mp_api.client.routes.materials.robocrys import RobocrysRester

from ..conftest import requires_api_key


@pytest.fixture
def rester():
    rester = RobocrysRester()
    yield rester
    rester.session.close()


@requires_api_key
def test_client(rester):
    search_method = rester.search

    if search_method is not None:
        q = {"keywords": ["silicon"], "num_chunks": 1}

        doc = search_method(**q)[0]

        assert doc.description is not None
        assert doc.condensed_structure is not None


@requires_api_key
def test_client_large_result_set(rester):
    search_method = rester.search

    if search_method is not None:
        q = {"keywords": ["Orthorhombic"], "num_chunks": 1}

        doc = search_method(**q)[0]

        assert doc.description is not None
        assert doc.condensed_structure is not None
