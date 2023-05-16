import os
import typing

import pytest
from emmet.core.molecules.summary import HasProps

from mp_api.client.routes.mpcules.summary import MoleculesSummaryRester

excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "has_solvent",
    "exclude_elements",
    # Below: currently timing out
    "nelements",
    "has_props",
]

alt_name = {"formula": "formula_alphabetical", "molecule_ids": "molecule_id"}

custom_field_tests = {
    "molecule_ids": ["9f153b9f3caa3124fb404b42e4cf82c8-C2H4-0-1"],
    "formula": "C2 H4",
    "chemsys": "C-H",
    "elements": ["C", "H"],
    "has_solvent": "DIELECTRIC=18,500;N=1,415;ALPHA=0,000;BETA=0,735;GAMMA=20,200;PHI=0,000;PSI=0,000",
    "has_level_of_theory": "wB97X-V/def2-TZVPPD/SMD",
    "has_lot_solvent": "wB97X-V/def2-TZVPPD/SMD(SOLVENT=THF)",
    "nelements": 2,
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
