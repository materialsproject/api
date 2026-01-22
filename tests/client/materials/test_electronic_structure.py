from ..conftest import client_search_testing, requires_api_key

import pytest
from pymatgen.analysis.magnetism import Ordering
from typing import Any

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.routes.materials.electronic_structure import (
    BandStructureRester,
    DosRester,
    ElectronicStructureRester,
)


@pytest.fixture
def es_rester():
    rester = ElectronicStructureRester()
    yield rester
    rester.session.close()


es_excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields: list[str] = []

es_alt_name_dict: dict[str, str] = {
    "material_ids": "material_id",
    "exclude_elements": "material_id",
    "formula": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}

es_custom_field_tests: dict[str, Any] = {
    "material_ids": ["mp-149"],
    "magnetic_ordering": Ordering.FM,
    "formula": "CoO2",
    "chemsys": "Co-O",
    "elements": ["Co", "O"],
    "exclude_elements": ["Co"],
}


@requires_api_key
def test_es_client(es_rester):
    search_method = es_rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=es_excluded_params,
        alt_name_dict=es_alt_name_dict,
        custom_field_tests=es_custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


bs_custom_field_tests = {
    "magnetic_ordering": Ordering.FM,
    "is_metal": True,
    "is_gap_direct": True,
    "efermi": (0, 100),
    "band_gap": (0, 5),
    "path_type": "hinuma",
}

bs_sub_doc_fields = ["bandstructure"]

bs_alt_name_dict: dict[str, str] = {}


@requires_api_key
def test_bs_client():
    # Get specific search method

    with BandStructureRester() as bs_rester:
        # Query fields
        for param in bs_custom_field_tests:
            project_field = bs_alt_name_dict.get(param, None)
            q = {
                param: bs_custom_field_tests[param],
                "chunk_size": 1,
                "num_chunks": 1,
            }
            doc = bs_rester.search(**q)[0].model_dump()

            for sub_field in bs_sub_doc_fields:
                if sub_field in doc:
                    doc = doc[sub_field]

            if param != "path_type":
                doc = doc["setyawan_curtarolo"]

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )

        with pytest.raises(MPRestError, match="No electronic structure data found."):
            _ = bs_rester.get_bandstructure_from_material_id("mp-0")

        with pytest.raises(MPRestError, match="No object found"):
            _ = bs_rester.get_bandstructure_from_task_id("mp-0")


dos_custom_field_tests = [
    {"magnetic_ordering": Ordering.FM},
    {"efermi": (1, 1.1)},
    {"band_gap": (8.0, 9.0)},
    {"projection_type": "elemental", "element": "As"},
    {
        "magnetic_ordering": "FM",
    },
]

dos_excluded_params = ["orbital", "element"]

dos_sub_doc_fields = ["dos"]

dos_alt_name_dict: dict[str, str] = {}


@requires_api_key
def test_dos_client():
    with DosRester() as dos_rester:
        # Query fields
        for params in dos_custom_field_tests:
            if any(param in dos_excluded_params for param in params):
                continue
            q = {
                **params,
                "chunk_size": 1,
                "num_chunks": 1,
            }
            doc = dos_rester.search(**q)[0].model_dump()
            for sub_field in dos_sub_doc_fields:
                if sub_field in doc:
                    doc = doc[sub_field]

            if not any(
                param in params for param in {"projection_type", "magnetic_ordering"}
            ):
                doc = doc["total"]["1"]

            assert all(
                doc[dos_alt_name_dict.get(param, param)] is not None for param in params
            )

        with pytest.raises(MPRestError, match="To query element-projected DOS"):
            _ = dos_rester.search(projection_type="elemental")

        with pytest.raises(MPRestError, match="To query orbital-projected DOS"):
            _ = dos_rester.search(projection_type="orbital")

        assert dos_rester.get_dos_from_material_id("mp-0") is None
        with pytest.raises(MPRestError, match="No object found"):
            _ = dos_rester.get_dos_from_task_id("mp-0")
