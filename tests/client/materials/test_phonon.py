import pytest
from emmet.core.phonon import PhononBS, PhononDOS

from mp_api._test_utils import client_search_testing, requires_api_key
from mp_api.client.core.exceptions import MPRestError
from mp_api.client.routes.materials.phonon import PhononRester


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
                "identifiers": "identifier",
                "material_ids": "identifier",
            },
            custom_field_tests={
                "material_ids": "mp-149",
                "identifiers": "mp-149",
                "phonon_method": "dfpt",
            },
            sub_doc_fields=[],
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_get_bandstructure_from_material_id(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    bs = rester.get_bandstructure_from_material_id(
        material_id="mp-149", phonon_method="dfpt"
    )
    assert isinstance(bs, PhononBS if use_document_model else dict)

    with pytest.raises(
        MPRestError,
        match="No phonon bandstructure data found for material ID mp-0",
    ):
        rester.get_bandstructure_from_material_id(
            material_id="mp-0", phonon_method="dfpt"
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_get_dos_from_material_id(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    dos = rester.get_dos_from_material_id(material_id="mp-149", phonon_method="dfpt")
    assert isinstance(dos, PhononDOS if use_document_model else dict)

    with pytest.raises(
        MPRestError,
        match="No phonon dos data found for material ID mp-0",
    ):
        rester.get_dos_from_material_id(material_id="mp-0", phonon_method="dfpt")


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_get_forceconstants_from_material_id(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    # Force constants are only produced by pheasy, not dfpt.
    fcs = rester.get_forceconstants_from_material_id(
        material_id="mp-149", phonon_method="pheasy"
    )
    assert isinstance(fcs, list)

    with pytest.raises(
        MPRestError,
        match="No phonon force constants data found for material ID mp-0",
    ):
        rester.get_forceconstants_from_material_id(
            material_id="mp-0", phonon_method="dfpt"
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_phonon_thermo(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    with pytest.raises(MPRestError, match="No phonon data found for material ID mp-0"):
        rester.compute_thermo_quantities(material_id="mp-0", phonon_method="dfpt")

    thermo_props = rester.compute_thermo_quantities(
        material_id="mp-149", phonon_method="dfpt"
    )

    # Default set in the method
    num_vals = 100

    assert all(
        isinstance(v, list) and len(v) == num_vals for v in thermo_props.values()
    )
