import os
from ..conftest import client_search_testing, requires_api_key

import pytest
from emmet.core.symmetry import CrystalSystem

from mp_api.client.routes.materials.materials import MaterialsRester
from mp_api.client.routes.materials import MATERIALS_RESTERS


@pytest.fixture
def rester():
    rester = MaterialsRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "exclude_elements",  # temp until server timeout increase
    "num_elements",  # temp until server timeout increase
    "num_sites",  # temp until server timeout increase
    "density",  # temp until server timeout increase
]

sub_doc_fields: list = []

alt_name_dict: dict = {
    "material_ids": "material_id",
    "formula": "material_id",
    "crystal_system": "symmetry",
    "spacegroup_number": "symmetry",
    "spacegroup_symbol": "symmetry",
    "exclude_elements": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}

custom_field_tests: dict = {
    "material_ids": ["mp-149"],
    "formula": "Si",
    "chemsys": "Si-P",
    "elements": ["Si", "P"],
    "task_ids": ["mp-149"],
    "crystal_system": CrystalSystem.cubic,
    "spacegroup_number": 38,
    "spacegroup_symbol": "Amm2",
}


@requires_api_key
def test_client(rester):
    search_method = rester.search

    assert sorted(dir(rester)) == sorted(
        dir(rester.__class__) + list(MATERIALS_RESTERS)
    )

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


@pytest.mark.xfail(condition=True, reason="Needs new deployment.", strict=False)
@pytest.mark.parametrize(
    "run_type, uncorrected_energy, use_document_model",
    [("PBE", None, True), ("r2SCAN", 1.0, False), ("GGA_U", (-50e4, 0.0), True)],
)
def test_blessed_entry(run_type, uncorrected_energy, use_document_model):
    # Si and NiO. Si has GGA and r2SCAN entries, NiO has GGA, GGA+U, and r2SCAN
    with MaterialsRester(use_document_model=use_document_model) as rester:
        blessed = rester.get_blessed_entries(
            run_type,
            material_ids=["mp-149", "mp-19009"],
            uncorrected_energy=uncorrected_energy,
        )

    assert all(
        isinstance(entry, dict)
        and all(entry.get(k) is not None for k in ("material_id", "blessed_entry"))
        for entry in blessed
    )
