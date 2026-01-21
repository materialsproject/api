import os

import numpy as np
import pytest

from emmet.core.phonon import PhononBS, PhononDOS

from mp_api.client.core.exceptions import MPRestError
from mp_api.client.routes.materials.phonon import PhononRester

from ..conftest import client_search_testing, requires_api_key


@requires_api_key
def test_phonon_search():
    with PhononRester() as rester:
        client_search_testing(
            search_method=rester.search,
            excluded_params=[
                "num_chunks",
                "chunk_size",
                "all_fields",
                "fields",
            ],
            alt_name_dict={
                "material_ids": "material_id",
            },
            custom_field_tests={
                "material_ids": ["mp-149", "mp-13"],
                "material_ids": "mp-149",
                "phonon_method": "dfpt",
            },
            sub_doc_fields=[],
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_phonon_get_methods(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    # TODO: update when there is force constant data
    for func_name, schema in {
        "bandstructure": PhononBS,
        "dos": PhononDOS,
        "forceconstants": list,
    }.items():
        args = tuple() if func_name == "forceconstants" else ("dfpt",)
        search_method = getattr(
            rester,
            f"get_{func_name}_from_material_id",
        )

        if func_name != "forceconstants":
            assert isinstance(
                search_method("mp-149", *args), schema if use_document_model else dict
            )

        with pytest.raises(MPRestError, match="No object found"):
            _ = search_method("mp-0", *args)


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_phonon_thermo(use_document_model):
    with pytest.raises(MPRestError, match="No phonon document found"):
        _ = PhononRester(
            use_document_model=use_document_model
        ).compute_thermo_quantities("mp-0", "dfpt")

    thermo_props = PhononRester(
        use_document_model=use_document_model
    ).compute_thermo_quantities("mp-149", "dfpt")

    # Default set in the method
    num_vals = 100

    assert all(
        isinstance(v, np.ndarray if k == "temperature" else list) and len(v) == num_vals
        for k, v in thermo_props.items()
    )
