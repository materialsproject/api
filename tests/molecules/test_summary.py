import os
from core_function import client_search_testing

import pytest
from emmet.core.molecules.summary import HasProps

from mp_api.client.routes.molecules.summary import MoleculesSummaryRester

excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "exclude_elements",
]

alt_name_dict = {"formula": "formula_alphabetical", "molecule_ids": "molecule_id"}

custom_field_tests = {
    "molecule_ids": ["351ef090ebd90b661a4e1205756f6957-C1Mg1N2O1S1-m2-1"],
    "formula": "C2 H4",
    "chemsys": "C-H",
    "elements": ["P"],
    "has_solvent": "DIELECTRIC=18,500;N=1,415;ALPHA=0,000;BETA=0,735;GAMMA=20,200;PHI=0,000;PSI=0,000",
    "has_level_of_theory": "wB97X-V/def2-TZVPPD/SMD",
    "has_lot_solvent": "wB97X-V/def2-TZVPPD/SMD(SOLVENT=THF)",
    "nelements": 2,
    "charge": 1,
    "spin_multiplicity": 1,
    "has_props": [HasProps.orbitals],
}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client():
    search_method = MoleculesSummaryRester().search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=[],
    )
