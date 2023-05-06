import os

import pytest

from mp_api.client import MPRester

# -- Rester name data for generic tests

key_only_resters = {
    "materials_phonon": "mp-11703",
    "materials_similarity": "mp-149",
    "doi": "mp-149",
    "materials_wulff": "mp-149",
    "materials_charge_density": "mp-1936745",
    "materials_provenance": "mp-149",
    "materials_robocrys": "mp-1025395",
}

search_only_resters = [
    "materials_grain_boundary",
    "materials_electronic_structure_bandstructure",
    "materials_electronic_structure_dos",
    "materials_substrates",
    "materials_synthesis",
]

special_resters = [
    "materials_charge_density",
]

ignore_generic = [
    "_user_settings",
    "_general_store",
    # "tasks",
    # "bonds",
    "materials_xas",
    "materials_elasticity",
    "materials_fermi",
    # "alloys",
    # "summary",
]  # temp


mpr = MPRester()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.parametrize("rester", mpr._all_resters)
def test_generic_get_methods(rester):
    # -- Test generic search and get_data_by_id methods
    name = rester.suffix.replace("/", "_")
    if name not in ignore_generic:
        if name not in key_only_resters:
            doc = rester._query_resource_data(
                {"_limit": 1}, fields=[rester.primary_key]
            )[0]
            assert isinstance(doc, rester.document_model)

            if name not in search_only_resters:
                doc = rester.get_data_by_id(
                    doc.dict()[rester.primary_key], fields=[rester.primary_key]
                )
                assert isinstance(doc, rester.document_model)

        elif name not in special_resters:
            doc = rester.get_data_by_id(
                key_only_resters[name], fields=[rester.primary_key]
            )
            assert isinstance(doc, rester.document_model)


if os.getenv("MP_API_KEY", None) is None:
    pytest.mark.skip(test_generic_get_methods)
