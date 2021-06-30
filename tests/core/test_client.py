import pytest
from mp_api.core.client import BaseRester


@pytest.fixture
def rester():
    rester = BaseRester()
    yield rester
    rester.session.close()


@pytest.mark.xfail
def test_post_fail(rester):
    rester._post_resource({}, suburl="materials/find_structure")

