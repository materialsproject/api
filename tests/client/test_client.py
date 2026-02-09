import warnings

import pytest

from mp_api.client import MPRester
from mp_api.client.routes.materials.tasks import TaskRester
from mp_api.client.routes.materials.provenance import ProvenanceRester

from .conftest import requires_api_key

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
    "materials_grain_boundaries",
    "materials_electronic_structure_bandstructure",
    "materials_electronic_structure_dos",
    "materials_substrates",
    "materials_synthesis",
    "materials_similarity",
    "materials_tasks",
]

special_resters = ["materials_charge_density", "doi"]

ignore_generic = [
    "_user_settings",
    "_general_store",
    "_messages",
    # "tasks",
    # "bonds",
    "materials_xas",
    "materials_elasticity",
    "materials_fermi",
    "materials_alloys",
    # "summary",
]  # temp


mpr = MPRester()

# Temporarily ignore molecules resters while molecules query operators are changed
resters_to_test = [
    rester
    for rester in mpr._all_resters
    if "molecule" not in rester._class_name.lower()
]


@requires_api_key
@pytest.mark.parametrize("rester", resters_to_test)
def test_generic_get_methods(rester):
    # -- Test generic search and get_data_by_id methods

    rester = rester(
        endpoint=mpr.endpoint,
        include_user_agent=True,
        session=mpr.session,
        use_document_model=True,
    )

    name = rester.suffix.replace("/", "_")

    docs_check = lambda _docs: all(
        rester.document_model.__module__ == _doc.__module__ for _doc in _docs
    )

    if name not in ignore_generic:
        key = rester.primary_key
        if name not in key_only_resters:
            if key not in rester.available_fields:
                key = rester.available_fields[0]

            doc = rester._query_resource_data({"_limit": 1}, fields=[key])[0]
            assert docs_check([doc])

            if name not in search_only_resters:
                docs = rester.search(
                    **{key + "s": [doc.model_dump()[key]]}, fields=[key]
                )
                assert docs_check(docs)

        elif name not in special_resters:
            search_method = "search"
            if name == "materials_robocrys":
                search_method += "_docs"
            docs = getattr(rester, search_method)(
                **{key + "s": [key_only_resters[name]]}, fields=[key]
            )
            with pytest.warns(DeprecationWarning, match="get_data_by_id is deprecated"):
                _ = rester.get_data_by_id(key_only_resters[name], fields=[key])

            assert docs_check(docs)
