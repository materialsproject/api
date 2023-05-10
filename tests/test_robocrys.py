from __future__ import annotations

import pytest

from mp_api.client.routes.robocrys import RobocrysRester
from tests import skip_if_no_api_key


@pytest.fixture
def rester():
    rester = RobocrysRester()
    yield rester
    rester.session.close()


@skip_if_no_api_key
def test_client(rester):
    search_method = rester.search

    if search_method is not None:
        q = {"keywords": ["silicon"], "num_chunks": 1}

        doc = search_method(**q)[0]

        assert doc.description is not None
        assert doc.condensed_structure is not None
