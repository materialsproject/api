import os
from core_function import client_search_testing

import pytest
from pymatgen.core.periodic_table import Element

from mp_api.client.routes.materials.electrodes import (
    ElectrodeRester,
    ConversionElectrodeRester,
)


@pytest.fixture
def insertion_rester():
    rester = ElectrodeRester()
    yield rester
    rester.session.close()


@pytest.fixture
def conversion_rester():
    rester = ConversionElectrodeRester()
    yield rester
    rester.session.close()


excluded_params = [
    "sort_fields",
    "chunk_size",
    "num_chunks",
    "all_fields",
    "fields",
]

sub_doc_fields = []  # type: list

alt_name_dict = {
    "battery_ids": "battery_id",
    "formula": "battery_id",
    "exclude_elements": "battery_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}  # type: dict

custom_field_tests = {
    "battery_ids": ["mp-16722_Al"],
    "working_ion": Element("Li"),
    "formula": "CoO2",
    "chemsys": "Co-O",
    "elements": ["Co", "O"],
    "exclude_elements": ["Co"],
}  # type: dict


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_insertion_client(insertion_rester):
    search_method = insertion_rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_conversion_client(conversion_rester):
    search_method = conversion_rester.search

    excl = ConversionElectrodeRester._exclude_search_fields
    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params + excl,
        alt_name_dict=alt_name_dict,
        custom_field_tests={
            "battery_ids": ["mp-1067_Al"],
            "working_ion": Element("Li"),
            "exclude_elements": ["Co", "O"],
        },
        sub_doc_fields=sub_doc_fields,
    )
