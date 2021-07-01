import os
from json import load
from mp_api.routes.synthesis.utils import (
    make_ellipsis,
    mask_paragraphs,
    mask_highlights,
)
from mp_api import MAPISettings
from mp_api.routes.synthesis.models.core import SynthesisSearchResultModel


def test_make_ellipsis():
    text = "Lorem ipsum dolor sit amet"
    altered_text = make_ellipsis(text, limit=10)
    assert altered_text == "Lorem ..."

    altered_text = make_ellipsis(text, limit=10, remove_trailing=False)
    assert altered_text == "... sit amet"


def test_mask_paragraphs():
    with open(os.path.join(MAPISettings().test_files, "synth_doc.json")) as file:
        synth_doc = load(file)

    doc = SynthesisSearchResultModel(**synth_doc)
    new_doc = mask_paragraphs(doc.dict(), limit=10)

    assert new_doc["paragraph_string"] == "Lorem ..."


def test_mask_highlights():
    with open(os.path.join(MAPISettings().test_files, "synth_doc.json")) as file:
        synth_doc = load(file)

    doc = SynthesisSearchResultModel(**synth_doc)
    new_doc = mask_highlights(doc.dict(), limit=10)
    assert new_doc["highlights"][0]["texts"][0]["value"] == "... anim ..."
