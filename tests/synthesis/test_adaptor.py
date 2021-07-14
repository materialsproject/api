import os
from json import load

from pymatgen.core import Composition

from mp_api import MAPISettings
from mp_api.routes.synthesis.data_adaptor import string2comp, convert_recipe


def test_string2comp():
    assert string2comp('BaTiO3') == Composition('BaTiO3')
    assert string2comp('LiOH·H2O') == Composition('LiOH')
    assert string2comp('TiO2·BaCO3') == Composition('TiO2')


def test_convert_recipe():
    with open(os.path.join(MAPISettings().test_files, "synth_doc_adaptor.json")) as file:
        synth_doc = load(file)

    converted = convert_recipe(synth_doc['src'])
    assert converted == synth_doc['product']
