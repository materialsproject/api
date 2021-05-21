import pytest
from mp_api.matproj import MPRester

key_only_resters = [
    "phonon",
    "phonon_img",
    "similarity",
    "doi",
    "wulff",
    "charge_density",
    "robocrys",
]


@pytest.mark.parametrize("rester", MPRester()._all_resters)
def test_search_clients(rester):
    if rester.endpoint.split("/")[-2] not in key_only_resters:
        doc = rester.query({"limit": 1}, fields=[rester.primary_key])[0]
        assert isinstance(doc, rester.document_model)
