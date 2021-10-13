import os
import pytest
from mp_api.matproj import MPRester

# -- Rester name data for generic tests

key_only_resters = {
    "phonon": "mp-11703",
    "similarity": "mp-149",
    "doi": "mp-149",
    "wulff": "mp-149",
    "charge_density": "mp-1936745",
    "provenance": "mp-149",
}

search_only_resters = [
    "grain_boundary",
    "electronic_structure_bandstructure",
    "electronic_structure_dos",
    "substrates",
    "synthesis",
]

special_resters = [
    "charge_density",
]

ignore_generic = ["robocrys", "_user_settings"]  # temp


mpr = MPRester()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.parametrize("rester", mpr._all_resters)
def test_generic_get_methods(rester):

    # -- Test generic search and get_document_by_id methods
    name = rester.suffix.replace("/", "_")
    if name not in ignore_generic:
        if name not in key_only_resters:
            doc = rester._query_resource_data(
                {"limit": 1}, fields=[rester.primary_key]
            )[0]
            assert isinstance(doc, rester.document_model)

            if name not in search_only_resters:
                doc = rester.get_document_by_id(
                    doc.dict()[rester.primary_key], fields=[rester.primary_key]
                )
                assert isinstance(doc, rester.document_model)

        elif name not in special_resters:
            doc = rester.get_document_by_id(
                key_only_resters[name], fields=[rester.primary_key]
            )
            assert isinstance(doc, rester.document_model)


if os.environ.get("MP_API_KEY", None) is None:
    pytest.mark.skip(test_generic_get_methods)
