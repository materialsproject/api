import os
from json import load

from pymatgen.core import Composition

from mp_api import MAPISettings
from mp_api.routes.synthesis.data_adaptor_synpro import convert_value, convert_conditions, convert_one, \
    get_material_formula


def test_convert_value():
    src = {
        "min": None,
        "max": 350.0,
        "values": [350.0],
        "tok_ids": [19],
        "units": "°C"
    }
    product = {
        'min_value': None,
        'max_value': 350.0,
        'values': [350.0],
        'units': "°C",
    }
    assert convert_value(src) == product


def test_conditions():
    src = {
        "temperature": [{"min": None, "max": 350.0, "values": [350.0], "tok_ids": [19], "units": "°C"}],
        "time": [{"max": 3.0, "min": 3.0, "values": [3.0], "tok_ids": [23], "units": "h"}],
        "environment": ["air", "O2"]
    }
    product = {
        'heating_temperature': [{'min_value': None, 'max_value': 350.0, 'values': [350.0], 'units': "°C", }],
        'heating_time': [{'min_value': 3.0, 'max_value': 3.0, 'values': [3.0], 'units': 'h'}],
        'heating_atmosphere': ["air", "O2"],
        'mixing_device': None,
        'mixing_media': None
    }
    assert convert_conditions(src, 'HeatingOperation') == product

    product = {
        'heating_temperature': [{'min_value': None, 'max_value': 350.0, 'values': [350.0], 'units': "°C", }],
        'heating_time': [{'min_value': 3.0, 'max_value': 3.0, 'values': [3.0], 'units': 'h'}],
        'heating_atmosphere': [],
        'mixing_device': 'O2',
        'mixing_media': 'air'
    }
    assert convert_conditions(src, 'MixingOperation') == product


def test_get_material_formula():
    assert get_material_formula({
        "material_formula": "NH4H2PO4",
        "composition": [
            {
                "formula": "NH4H2PO4",
                "amount": "1",
                "elements": {
                    "N": "1",
                    "H": "6",
                    "P": "1",
                    "O": "4"
                },
            }
        ],
    }) == Composition('NH4H2PO4')

    assert get_material_formula({
        "material_formula": "TiO2-2BaCO3",
        "composition": [
            {
                "formula": "TiO2",
                "amount": "1",
                "elements": {
                    "Ti": "1",
                    "O": "2"
                },
            },
            {
                "formula": "BaCO3",
                "amount": "2",
                "elements": {
                    "Ba": "1",
                    "C": "1",
                    "O": "3"
                },
            }
        ],
    }) == Composition('TiBa2C2O8')


def test_convert_one():
    with open(os.path.join(MAPISettings().test_files, "synth_doc_adaptor_synpro.json")) as file:
        synth_doc = load(file)

    assert convert_one(synth_doc['src']) == synth_doc['product']
