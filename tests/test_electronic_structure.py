import os
import pytest
from mp_api.client.routes.electronic_structure import (
    BandStructureRester,
    DosRester,
    ElectronicStructureRester,
)

from pymatgen.analysis.magnetism import Ordering

import inspect
import typing


@pytest.fixture
def es_rester():
    rester = ElectronicStructureRester()
    yield rester
    rester.session.close()


es_excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields = []  # type: list

es_alt_name_dict = {
    "material_ids": "material_id",
    "exclude_elements": "material_id",
    "formula": "material_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}  # type: dict

es_custom_field_tests = {
    "material_ids": ["mp-149"],
    "magnetic_ordering": Ordering.FM,
    "formula": "CoO2",
    "chemsys": "Co-O",
    "elements": ["Co", "O"],
    "exclude_elements": ["Co"],
}  # type: dict


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_es_client(es_rester):
    search_method = es_rester.search

    if search_method is not None:
        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and boolean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in es_excluded_params:

                param_type = entry[1].__args__[0]
                q = None

                if param in es_custom_field_tests:
                    project_field = es_alt_name_dict.get(param, None)
                    q = {
                        param: es_custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type == typing.Tuple[int, int]:
                    project_field = es_alt_name_dict.get(param, None)
                    q = {
                        param: (-1000, 1000),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type == typing.Tuple[float, float]:
                    project_field = es_alt_name_dict.get(param, None)
                    q = {
                        param: (-1000.1234, 1000.1234),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is bool:
                    project_field = es_alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }

                doc = search_method(**q)[0].dict()

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )


bs_custom_field_tests = {
    "magnetic_ordering": Ordering.FM,
    "is_metal": True,
    "is_gap_direct": True,
    "efermi": (0, 100),
    "band_gap": (0, 5),
}

bs_sub_doc_fields = ["bandstructure"]

bs_alt_name_dict = {}  # type: dict


@pytest.fixture
def bs_rester():
    rester = BandStructureRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_bs_client(bs_rester):
    # Get specific search method
    search_method = bs_rester.search

    # Query fields
    for param in bs_custom_field_tests:
        project_field = bs_alt_name_dict.get(param, None)
        q = {
            param: bs_custom_field_tests[param],
            "chunk_size": 1,
            "num_chunks": 1,
        }
        doc = search_method(**q)[0].dict()

        for sub_field in bs_sub_doc_fields:
            if sub_field in doc:
                doc = doc[sub_field]

        if param != "path_type":
            doc = doc["setyawan_curtarolo"]

        assert doc[project_field if project_field is not None else param] is not None


dos_custom_field_tests = {
    "magnetic_ordering": Ordering.FM,
    "efermi": (0, 100),
    "band_gap": (0, 5),
}

dos_excluded_params = ["orbital", "element"]

dos_sub_doc_fields = ["dos"]

dos_alt_name_dict = {}  # type: dict


@pytest.fixture
def dos_rester():
    rester = DosRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_dos_client(dos_rester):
    search_method = dos_rester.search

    # Query fields
    for param in dos_custom_field_tests:
        if param not in dos_excluded_params:
            project_field = dos_alt_name_dict.get(param, None)
            q = {
                param: dos_custom_field_tests[param],
                "chunk_size": 1,
                "num_chunks": 1,
            }
            doc = search_method(**q)[0].dict()
            for sub_field in dos_sub_doc_fields:
                if sub_field in doc:
                    doc = doc[sub_field]

            if param != "projection_type" and param != "magnetic_ordering":
                doc = doc["total"]["1"]

            assert (
                doc[project_field if project_field is not None else param] is not None
            )
