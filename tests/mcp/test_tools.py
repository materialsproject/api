import numpy as np
from pymatgen.core import Composition
import pytest

from mp_api.mcp._schemas import SearchOutput, FetchResult, MaterialMetadata
from mp_api.mcp.tools import MPCoreMCP


def test_chem_sys_parsing():
    for user_input, expected_output in {
        "mp-149": {},
        "LiFePO4": {"formula": Composition("LiFePO4").formula},
        "Cs-Cl": {"chemsys": "Cl-Cs"},
    }.items():
        assert (
            MPCoreMCP._validate_chemical_system_formula(user_input) == expected_output
        )


def test_core_search_tools():
    with MPCoreMCP() as mcp_tools:
        search_results = mcp_tools.search("Ga-W")
        robo_desc_docs = mcp_tools.client.materials.robocrys.search_docs(
            material_ids=[doc.id for doc in search_results.results],
            fields=["material_id", "description"],
        )
    robo_descs = {doc["material_id"]: doc["description"] for doc in robo_desc_docs}

    assert isinstance(search_results, SearchOutput)
    assert all(
        isinstance(doc, FetchResult)
        and doc.id.startswith("mp-")
        and doc.metadata is None
        and doc.title.startswith("mp-")
        and doc.text == robo_descs[doc.id]
        and doc.url == f"https://next-gen.materialsproject.org/materials/{doc.id}"
        for doc in search_results.results
    )


def test_core_fetch_tools():
    with MPCoreMCP() as mcp_tools:
        fetch_results = mcp_tools.fetch("Ir2 Br6")
        fetch_many_results = mcp_tools.fetch_many("Ir2 Br6")
        ref_struct = mcp_tools.client.get_structure_by_material_id(fetch_results.id)

        robo_desc_docs = mcp_tools.client.materials.robocrys.search_docs(
            material_ids=[fetch_results.id], fields=["material_id", "description"]
        )
        assert all(
            isinstance(doc, FetchResult) for doc in mcp_tools.fetch_many("mp-13, LiF")
        )

    assert fetch_many_results[0] == fetch_results

    assert isinstance(fetch_results, FetchResult)
    assert isinstance(fetch_results.metadata, MaterialMetadata)
    assert isinstance(fetch_results.metadata.structurally_similar_materials, str)
    assert (
        fetch_results.text
        == next(
            doc for doc in robo_desc_docs if doc["material_id"] == fetch_results.id
        )["description"]
    )

    assert np.allclose(
        ref_struct.lattice.matrix,
        fetch_results.metadata.cell_vectors,
    )
    assert np.allclose(
        ref_struct.cart_coords,
        fetch_results.metadata.cartesian_coordinates,
    )
    assert fetch_results.metadata.atoms == [
        str(site.species.elements[0]) for site in ref_struct
    ]
    if magmoms := ref_struct.site_properties.get("magmom"):
        assert fetch_results.metadata.magnetic_moments == pytest.approx(magmoms)
    else:
        assert fetch_results.metadata.magnetic_moments is None


def test_core_phase_diagram_tool():
    from plotly.graph_objects import Figure

    with MPCoreMCP() as mcp_tools:
        assert isinstance(mcp_tools.get_phase_diagram_from_elements("Li, F"), Figure)
