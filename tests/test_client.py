import os

import pytest

from mp_api.client import MPRester
from mp_api.client.routes.materials import TaskRester, ProvenanceRester

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
    "_messages",
    # "tasks",
    # "bonds",
    "materials_xas",
    "materials_elasticity",
    "materials_fermi",
    # "alloys",
    # "summary",
]  # temp


mpr = MPRester()

# Temporarily ignore molecules resters while molecules query operators are changed
resters_to_test = [
    rester for rester in mpr._all_resters if "molecule" not in rester.suffix
]


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.parametrize("rester", resters_to_test)
def test_generic_get_methods(rester):
    # -- Test generic search and get_data_by_id methods
    name = rester.suffix.replace("/", "_")

    rester = rester(
        endpoint=mpr.endpoint,
        include_user_agent=True,
        session=mpr.session,
        monty_decode=True
        if rester not in [TaskRester, ProvenanceRester]  # type: ignore
        else False,  # Disable monty decode on nested data which may give errors
        use_document_model=True,
    )

    if name not in ignore_generic:
        if name not in key_only_resters:
            doc = rester._query_resource_data(
                {"_limit": 1}, fields=[rester.primary_key]
            )[0]
            assert isinstance(doc, rester.document_model)

            if name not in search_only_resters:
                doc = rester.get_data_by_id(
                    doc.model_dump()[rester.primary_key], fields=[rester.primary_key]
                )
                assert isinstance(doc, rester.document_model)

        elif name not in special_resters:
            doc = rester.get_data_by_id(
                key_only_resters[name], fields=[rester.primary_key]
            )
            assert isinstance(doc, rester.document_model)


if os.getenv("MP_API_KEY", None) is None:
    pytest.mark.skip(test_generic_get_methods)
