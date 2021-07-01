import pytest
from mp_api.routes.synthesis.client import SynthesisRester

import inspect


@pytest.fixture
def rester():
    rester = SynthesisRester()
    yield rester
    rester.session.close()


def test_client(rester):
    # Get specific search method
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:

        q = {"keywords": ["silicon"]}

        doc = search_method(**q)[0]

        assert doc.doi is not None
        assert doc.paragraph_string is not None
        assert doc.synthesis_type is not None

