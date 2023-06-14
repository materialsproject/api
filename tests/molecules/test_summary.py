import os
import typing

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

alt_name = {"formula": "formula_alphabetical", "molecule_ids": "molecule_id"}

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

    # Get list of parameters
    param_tuples = list(typing.get_type_hints(search_method).items())

    # Query API for each numeric and boolean parameter and check if returned
    for entry in param_tuples:
        param = entry[0]
        if param not in excluded_params:
            param_type = entry[1].__args__[0]
            q = None

            print(param)

            if param in custom_field_tests:
                q = {
                    param: custom_field_tests[param],
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type == typing.Tuple[int, int]:
                q = {
                    param: (-100, 100),
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type == typing.Tuple[float, float]:
                q = {
                    param: (-3000.12, 3000.12),
                    "chunk_size": 1,
                    "num_chunks": 1,
                }
            elif param_type is bool:
                q = {
                    param: False,
                    "chunk_size": 1,
                    "num_chunks": 1,
                }

            docs = search_method(**q)

            if len(docs) > 0:
                doc = docs[0].dict()
            else:
                raise ValueError("No documents returned")

            assert doc[alt_name.get(param, param)] is not None
