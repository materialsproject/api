import os
import pytest
from mp_api.routes.robocrys.client import RobocrysRester

import inspect
import typing
from pymatgen.core.periodic_table import Element


@pytest.fixture
def rester():
    rester = RobocrysRester()
    yield rester
    rester.session.close()


@pytest.mark.xfail  # temp
@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client(rester):
    # Get specific search method
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:

        q = {"keywords": ["silicon", "process"]}

        doc = search_method(**q)[0]

        assert doc.description is not None
        assert doc.condensed_structure is not None
        assert doc.task_id is not None
