import os
from typing import List

import pytest
from emmet.core.synthesis import SynthesisRecipe, SynthesisTypeEnum

from mp_api.client.routes.materials.synthesis import SynthesisRester


@pytest.fixture
def rester():
    rester = SynthesisRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_client(rester):
    search_method = rester.search

    if search_method is not None:
        q = {"keywords": ["silicon"]}

        doc = search_method(**q)[0]

        assert doc.doi is not None
        assert doc.paragraph_string is not None
        assert doc.synthesis_type is not None


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_filters_keywords(rester):
    search_method = rester.search

    if search_method is not None:
        doc = search_method(keywords=["silicon"])[0]

        assert isinstance(doc.search_score, float)
        highlighted = sum((x["texts"] for x in doc.highlights), [])
        assert "silicon" in " ".join([x["value"] for x in highlighted]).lower()


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_filters_synthesis_type(rester):
    search_method = rester.search

    if search_method is not None:
        doc = search_method(
            synthesis_type=[SynthesisTypeEnum.solid_state], num_chunks=1
        )
        assert all(x.synthesis_type == SynthesisTypeEnum.solid_state for x in doc)

        doc = search_method(synthesis_type=[SynthesisTypeEnum.sol_gel], num_chunks=1)
        assert all(x.synthesis_type == SynthesisTypeEnum.sol_gel for x in doc)


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
@pytest.mark.xfail  # Needs fixing
def test_filters_temperature_range(rester):
    search_method = rester.search

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_temperature_min=700,
            condition_heating_temperature_max=1000,
            num_chunks=5,
        )
        for doc in docs:
            for op in doc.operations:
                for temp in op.conditions.heating_temperature:
                    for val in temp.values:
                        assert 700 <= val <= 1000


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
@pytest.mark.xfail  # Needs fixing
def test_filters_time_range(rester):
    search_method = rester.search

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_time_min=7, condition_heating_time_max=11, num_chunks=5
        )
        for doc in docs:
            for op in doc.operations:
                for temp in op.conditions.heating_time:
                    for val in temp.values:
                        assert 7 <= val <= 11


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_filters_atmosphere(rester):
    search_method = rester.search

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_heating_atmosphere=["air", "O2"],
            num_chunks=5,
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                for atm in op.conditions.heating_atmosphere:
                    if atm in ["air", "O2"]:
                        found = True
            assert found


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_filters_mixing_device(rester):
    search_method = rester.search

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_mixing_device=["zirconia", "Al2O3"],
            num_chunks=5,
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                if op.conditions.mixing_device in ["zirconia", "Al2O3"]:
                    found = True
            assert found


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
def test_filters_mixing_media(rester):
    search_method = rester.search

    if search_method is not None:
        docs: List[SynthesisRecipe] = search_method(
            condition_mixing_media=["water", "alcohol"],
            num_chunks=5,
        )
        for doc in docs:
            found = False
            for op in doc.operations:
                if op.conditions.mixing_media in ["water", "alcohol"]:
                    found = True
            assert found
