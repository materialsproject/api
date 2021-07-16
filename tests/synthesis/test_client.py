import inspect
import os
from typing import List

import pytest

from mp_api.routes.synthesis.client import SynthesisRester
from mp_api.routes.synthesis.models import SynthesisTypeEnum, SynthesisRecipe


@pytest.fixture
def rester():
    rester = SynthesisRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_client(rester):
    # Get specific search method
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        q = {"keywords": ["silicon"]}

        doc = search_method(**q)[0]

        assert doc.doi is not None
        assert doc.paragraph_string is not None
        assert doc.synthesis_type is not None


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_filters_keywords(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        doc = search_method(keywords=["silicon"])[0]

        assert isinstance(doc.search_score, float)
        highlighted = sum([x["texts"] for x in doc.highlights], [])
        assert "silicon" in " ".join([x["value"] for x in highlighted]).lower()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_filters_synthesis_type(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        doc = search_method(synthesis_type=[SynthesisTypeEnum.solid_state])
        assert all(x.synthesis_type == SynthesisTypeEnum.solid_state for x in doc)

        doc = search_method(synthesis_type=[SynthesisTypeEnum.sol_gel])
        assert all(x.synthesis_type == SynthesisTypeEnum.sol_gel for x in doc)


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.xfail  # Needs fixing
def test_filters_temperature_range(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_temperature_min=700,
            condition_heating_temperature_max=1000,
        )
        for doc in docs:
            for op in doc.operations:
                for temp in op.conditions.heating_temperature:
                    for val in temp.values:
                        assert 700 <= val <= 1000


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.xfail  # Needs fixing
def test_filters_time_range(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_time_min=7, condition_heating_time_max=11,
        )
        for doc in docs:
            for op in doc.operations:
                for temp in op.conditions.heating_time:
                    for val in temp.values:
                        assert 7 <= val <= 11


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
@pytest.mark.xfail  # Needs fixing
def test_filters_atmosphere(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_atmosphere=["air", "O2"],
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                for atm in op.conditions.heating_atmosphere:
                    if atm in ["air", "O2"]:
                        found = True
            assert found


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_filters_mixing_device(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_mixing_device=["zirconia", "Al2O3"],
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                if op.conditions.mixing_device in ["zirconia", "Al2O3"]:
                    found = True
            assert found


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
def test_filters_mixing_media(rester):
    search_method = None
    for entry in inspect.getmembers(rester, predicate=inspect.ismethod):
        if "search" in entry[0] and entry[0] != "search":
            search_method = entry[1]

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_mixing_media=["water", "alcohol"],
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                if op.conditions.mixing_media in ["water", "alcohol"]:
                    found = True
            assert found
