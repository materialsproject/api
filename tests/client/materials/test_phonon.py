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
        match="No phonon data found for material ID mp-0",
    ):
        rester.get_bandstructure_from_material_id(
            material_id="mp-0", phonon_method="dfpt"
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_phonon_method_is_chosen_from_the_data(use_document_model):
    """Most materials only have pheasy data, a few only dfpt, a few both."""
    rester = PhononRester(use_document_model=use_document_model)
    expected = PhononBS if use_document_model else dict

    # pheasy only
    assert isinstance(
        rester.get_bandstructure_from_material_id("mp-aaahikjt"), expected
    )
    # dfpt only
    assert isinstance(rester.get_bandstructure_from_material_id("mp-2172"), expected)
    # both: either can be asked for
    assert isinstance(rester.get_bandstructure_from_material_id("mp-149"), expected)
    assert isinstance(
        rester.get_bandstructure_from_material_id("mp-149", phonon_method="dfpt"),
        expected,
    )

    # a method that was asked for is never replaced by another
    with pytest.raises(
        MPRestError, match=r"No dfpt phonon data for mp-aaahikjt \(available: pheasy\)"
    ):
        rester.get_bandstructure_from_material_id("mp-aaahikjt", phonon_method="dfpt")


@requires_api_key
def test_phonon_bandstructure_path_types():
    rester = PhononRester()

    # pheasy should have all k-path conventions
    for path_type in ("setyawan_curtarolo", "hinuma", "latimer_munro"):
        bs = rester.get_bandstructure_from_material_id(
            "mp-aaahikjt", path_type=path_type
        )
        assert isinstance(bs, PhononBS)

    # dfpt only has one
    with pytest.raises(MPRestError, match="only available with path_type"):
        rester.get_bandstructure_from_material_id("mp-2172", path_type="hinuma")


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_get_dos_from_material_id(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    dos = rester.get_dos_from_material_id(material_id="mp-149", phonon_method="dfpt")
    assert isinstance(dos, PhononDOS if use_document_model else dict)

    # the method defaults to what the material has
    for material_id in ("mp-aaahikjt", "mp-2172", "mp-149"):
        dos = rester.get_dos_from_material_id(material_id=material_id)
        assert isinstance(dos, PhononDOS if use_document_model else dict)

    with pytest.raises(
        MPRestError,
        match="No phonon data found for material ID mp-0",
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
        match="No phonon data found for material ID mp-0",
    ):
        rester.get_forceconstants_from_material_id(
            material_id="mp-0", phonon_method="pheasy"
        )

    with pytest.raises(
        MPRestError, match="dfpt phonon calculations have no force constants"
    ):
        rester.get_forceconstants_from_material_id(
            material_id="mp-149", phonon_method="dfpt"
        )


@requires_api_key
@pytest.mark.parametrize("use_document_model", [True, False])
def test_phonon_thermo(use_document_model):
    rester = PhononRester(use_document_model=use_document_model)

    with pytest.raises(MPRestError, match="No phonon data found for material ID mp-0"):
        rester.compute_thermo_quantities(material_id="mp-0", phonon_method="dfpt")

    # Default set in the method
    num_vals = 100

    # with and without choosing the method (pheasy-only, dfpt-only, both)
    for kwargs in (
        {"material_id": "mp-149", "phonon_method": "dfpt"},
        {"material_id": "mp-149"},
        {"material_id": "mp-aaahikjt"},
        {"material_id": "mp-2172"},
    ):
        thermo_props = rester.compute_thermo_quantities(**kwargs)
        assert all(
            isinstance(v, list) and len(v) == num_vals for v in thermo_props.values()
        )
