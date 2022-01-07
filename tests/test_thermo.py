import os
from pymatgen.analysis.phase_diagram import PhaseDiagram
import pytest
from mp_api.routes.thermo import ThermoRester

import inspect
import typing

resters = [ThermoRester()]

excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
    "equilibrium_reaction_energy",
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "formula": "formula_pretty",
    "material_ids": "material_id",
    "total_energy": "energy_per_atom",
    "formation_energy": "formation_energy_per_atom",
    "uncorrected_energy": "uncorrected_energy_per_atom",
    "equilibirum_reaction_energy": "equilibirum_reaction_energy_per_atom",
}  # type: dict

custom_field_tests = {
    "material_ids": ["mp-149"],
    "formula": "SiO2",
    "chemsys": "Si-O",
}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.parametrize("rester", resters)
def test_client(rester):
    # Get specific search method
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and boolean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in excluded_params:
                param_type = entry[1].__args__[0]
                q = None

                if param_type == typing.Tuple[int, int]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param_type == typing.Tuple[float, float]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100.12, 100.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param_type is bool:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }
                elif param in custom_field_tests:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                        "fields": [
                            project_field if project_field is not None else param
                        ],
                    }

                doc = search_method(**q)[0].dict()
                for sub_field in sub_doc_fields:
                    if sub_field in doc:
                        doc = doc[sub_field]

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )


@pytest.mark.xfail(reason="Monty decode issue with phase diagram")
def test_get_phase_diagram_from_chemsys():
    # Test that a phase diagram is returned

    assert isinstance(
        ThermoRester().get_phase_diagram_from_chemsys("Hf-Pm"), PhaseDiagram
    )
