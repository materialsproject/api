import os

import numpy as np
import pytest

from emmet.core.similarity import SimilarityScorer, SimilarityEntry
from pymatgen.core import Structure

from mp_api.client.core import MPRestError
from mp_api.client.routes.materials.similarity import SimilarityRester

from ..conftest import client_search_testing, requires_api_key

try:
    import matminer
except ImportError:
    matminer = None


@pytest.fixture(scope="module")
def test_struct():
    poscar = """Al2
1.0
   3.3335729972004917    0.0000000000000000    1.9246389981090721
   1.1111909992801432    3.1429239987499362    1.9246389992542632
   0.0000000000000000    0.0000000000000000    3.8492780000000000
Al
2
direct
   0.875    0.875    0.875 Al
   0.125    0.125    0.125 Al
"""
    return Structure.from_str(poscar, fmt="poscar")


@requires_api_key
def test_similarity_search():
    client_search_testing(
        search_method=SimilarityRester().search,
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
        },
        sub_doc_fields=[],
    )


@requires_api_key
def test_similarity_vector_search(test_struct):
    rester = SimilarityRester()

    # skip these tests if `matminer` is not installed
    if matminer is not None:
        fv = rester.fingerprint_structure(test_struct)
        assert isinstance(fv, np.ndarray)
        assert len(fv) == 122
        assert isinstance(rester._fingerprinter, SimilarityScorer)

        assert all(
            isinstance(entry, SimilarityEntry)
            and isinstance(entry.dissimilarity, float)
            for entry in rester.find_similar(
                test_struct,
                top=2,
            )
        )

    get_top = 5
    sim_entries = rester.find_similar("mp-149", top=get_top)
    assert all(isinstance(entry, SimilarityEntry) for entry in sim_entries)
    assert len(sim_entries) == get_top

    sim_dict_entries = SimilarityRester(use_document_model=False).find_similar(
        "mp-149", top=get_top
    )
    assert all(
        isinstance(entry, dict)
        and all(k in entry for k in SimilarityEntry.model_fields)
        for entry in sim_dict_entries
    )

    with pytest.raises(MPRestError, match="No similarity data available for"):
        _ = rester.find_similar("mp-0")

    with pytest.raises(
        MPRestError, match="Please submit a pymatgen Structure or MP ID"
    ):
        _ = rester.find_similar(np.random.rand(122))
