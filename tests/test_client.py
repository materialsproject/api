from mp_api.matproj import MPRester

from pymatgen.entries import Entry


def test_thermo_get_entries():

    with MPRester() as mpr:
        thermo_doc = mpr.thermo.get_document_by_id("mp-804")

    assert isinstance(thermo_doc.thermo.entry, Entry)