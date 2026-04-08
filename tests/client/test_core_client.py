import pytest

import json

from mp_api._test_utils import requires_api_key

from mp_api.client import MPRester
from mp_api.client.core import BaseRester
from mp_api.client.core.exceptions import MPRestError, MPRestWarning
from mp_api.client.routes.materials.materials import MaterialsRester



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
    assert rester.available_fields == []


def test_fields_not_requested_excludes_requested_fields(mpr):
    task_rester = mpr.materials.tasks
    doc = {"task_id": "fakeid-1234", "state": "successful"}
    requested_fields = list(task_rester.document_model.model_fields)

    doc_model, _, fields_not_requested = task_rester._generate_returned_model(
        doc, requested_fields=requested_fields
    )
    deser_doc = doc_model(**doc)

    assert "dir_name" not in fields_not_requested
    assert "tags" in deser_doc.unavailable_fields
    with pytest.raises(AttributeError, match="is unavailable in the returned data"):
        deser_doc.tags

    requested_fields.remove("tags")
    doc_model, _, _ = task_rester._generate_returned_model(
        doc, requested_fields=requested_fields
    )
    deser_doc = doc_model(**doc)
    with pytest.raises(
        AttributeError, match="data is available but has not been requested in"
    ):
        deser_doc.tags

    with pytest.raises(AttributeError, match="object has no attribute 'fake_field'"):
        deser_doc.fake_field

    assert all(
        substr in str(deser_doc)
        for substr in ("MPDataDoc", "CoreTaskDoc", "task_id", "Fields not requested")
    )
    assert all(
        substr in deser_doc.__repr__()
        for substr in ("MPDataDoc", "CoreTaskDoc", "task_id", "fields_not_requested")
    )
    assert deser_doc.dict() == deser_doc.model_dump()
    assert isinstance(json.dumps(deser_doc.dict()), str)


def test_warnings_exceptions():
    with pytest.warns(MPRestWarning, match="Ignoring `monty_decode`"):
        MaterialsRester(monty_decode=True)

    with pytest.raises(MPRestError, match="Chunk size must be greater than zero"):
        MaterialsRester()._get_all_documents({}, chunk_size=-1)

    with pytest.raises(MPRestError, match="Number of chunks must be greater than zero"):
        MaterialsRester()._get_all_documents({}, num_chunks=-1)
