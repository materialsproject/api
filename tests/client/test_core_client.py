import pytest

from mp_api.client import MPRester
from mp_api.client.core import BaseRester

from .conftest import requires_api_key


@pytest.fixture
def rester():
    rester = BaseRester()
    yield rester
    rester.session.close()


@pytest.fixture()
def mpr():
    rester = MPRester()
    yield rester
    rester.session.close()


@requires_api_key
@pytest.mark.xfail
def test_post_fail(rester):
    rester._post_resource({}, suburl="materials/find_structure")


@requires_api_key
def test_pagination(mpr):
    mpids = mpr.materials.search(
        all_fields=False, fields=["material_id"], num_chunks=2, chunk_size=1000
    )
    assert len(mpids) > 1000


@requires_api_key
def test_count(mpr):
    count = mpr.materials.count(
        dict(task_ids="mp-149", _all_fields=False, _fields="material_id")
    )
    assert count == 1


def test_available_fields(rester, mpr):
    assert len(mpr.materials.available_fields) > 0
    assert rester.available_fields == ["Unknown fields."]
