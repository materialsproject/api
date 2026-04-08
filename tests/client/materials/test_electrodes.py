import os

import pytest
from pymatgen.core.periodic_table import Element

from mp_api._test_utils import client_search_testing, client_pagination, client_sort, requires_api_key

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
    "_page",
    "_sort_fields",
]

sub_doc_fields: list = []

alt_name_dict: dict = {
    "battery_ids": "battery_id",
    "formula": "battery_id",
    "exclude_elements": "battery_id",
    "num_elements": "nelements",
    "num_sites": "nsites",
}

custom_field_tests: dict = {
    "battery_ids": ["mp-16722_Al"],
    "working_ion": Element("Li"),
    "formula": "CoO2",
    "chemsys": "Co-O",
    "elements": ["Co", "O"],
    "exclude_elements": ["Co"],
}


@requires_api_key
def test_insertion_client(insertion_rester):
    search_method = insertion_rester.search

    client_search_testing(
        search_method=search_method,
        excluded_params=excluded_params,
        alt_name_dict=alt_name_dict,
        custom_field_tests=custom_field_tests,
        sub_doc_fields=sub_doc_fields,
    )


@requires_api_key
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
        },
        sub_doc_fields=sub_doc_fields,
    )


@requires_api_key
def test_pagination():
    with ElectrodeRester() as rester:
        client_pagination(rester.search,"battery_id")

@pytest.mark.xfail(reason="Sort requires API redeployment", strict=False)
@requires_api_key
@pytest.mark.parametrize("sort_field",["battery_id","stability_charge","average_voltage"])
def test_sort(sort_field):
    with ElectrodeRester() as rester:
        client_sort(rester.search,sort_field)