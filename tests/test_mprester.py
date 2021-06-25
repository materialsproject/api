import pytest
import random
import os
from mp_api.matproj import MPRester
from mp_api.core.settings import MAPISettings
import requests

from pymatgen.io.cif import CifParser
from pymatgen.electronic_structure.bandstructure import (
    BandStructure,
    BandStructureSymmLine,
)
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.core.periodic_table import Element
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.io.vasp import Incar, Chgcar

api_is_up = (
    requests.get("https://api.materialsproject.org/heartbeat").status_code == 200
)


@pytest.fixture()
def mpr():
    rester = MPRester()
    yield rester
    rester.session.close()


# @pytest.mark.skipif(((os.environ.get("MP_API_KEY", None) is None) or (not api_is_up)))
class TestMPRester:
    def test_get_structure_by_material_id(self, mpr):
        s1 = mpr.get_structure_by_material_id("mp-1")
        assert s1.formula == "Cs2"

        s1 = mpr.get_structure_by_material_id("mp-4163", conventional_unit_cell=True)
        assert s1.formula == "Ca12 Ti8 O28"

        s1 = mpr.get_structure_by_material_id("mp-149", final=False)
        assert [s.formula for s in s1] == ["Si2"]

        # # requesting via task-id instead of mp-id
        with pytest.warns(UserWarning):
            mpr.get_structure_by_material_id("mp-698856")

    def test_get_database_version(self, mpr):
        db_version = mpr.get_database_version()
        assert db_version == MAPISettings().db_version

    def test_get_materials_id_from_task_id(self, mpr):
        assert mpr.get_materials_id_from_task_id("mp-540081") == "mp-19017"

    # TODO: add method to MPRester
    # def test_get_materials_id_references(self, mpr):
    #     data = mpr.get_materials_id_references("mp-123")
    #     assert len(data) > 1000

    def test_get_materials_ids_doc(self, mpr):
        mpids = mpr.get_materials_ids("Al2O3")
        random.shuffle(mpids)
        doc = mpr.materials.get_document_by_id(mpids.pop(0))
        assert doc.formula_pretty == "Al2O3"

    def test_get_structures(self, mpr):
        structs = mpr.get_structures("Mn3O4")
        assert len(structs) > 0

        structs = mpr.get_structures("Mn3O4", final=False)
        assert len(structs) > 0

    def test_find_structure(self, mpr):
        path = os.path.join(MAPISettings().test_files, "Si_mp_149.cif")
        with open(path) as file:
            data = mpr.find_structure(path)
            assert len(data) > 0

            s = CifParser(file).get_structures()[0]
            data = mpr.find_structure(s)
            assert len(data) > 0

    def test_get_bandstructure_by_material_id(self, mpr):
        bs = mpr.get_bandstructure_by_material_id("mp-149")
        assert isinstance(bs, BandStructureSymmLine)
        bs_unif = mpr.get_bandstructure_by_material_id("mp-149", line_mode=False)
        assert isinstance(bs_unif, BandStructure)
        assert not isinstance(bs_unif, BandStructureSymmLine)

    def test_get_dos_by_id(self, mpr):
        dos = mpr.get_dos_by_material_id("mp-149")
        assert isinstance(dos, CompleteDos)

    def test_get_entry_by_material_id(self, mpr):
        e = mpr.get_entry_by_material_id("mp-19017")
        assert isinstance(e[0], ComputedEntry)
        assert e[0].composition.reduced_formula == "LiFePO4"

    def test_get_entries(self, mpr):
        syms = ["Li", "Fe", "O"]
        chemsys = "Li-Fe-O"
        entries = mpr.get_entries(chemsys)
        sorted_entries = mpr.get_entries(chemsys, sort_by_e_above_hull=True)

        elements = set([Element(sym) for sym in syms])
        for e in entries:
            assert isinstance(e, ComputedEntry)
            assert set(e.composition.elements).issubset(elements)

        assert sorted_entries != entries

    def test_get_phonon_data_by_material_id(self, mpr):
        bs = mpr.get_phonon_bandstructure_by_material_id("mp-661")
        assert isinstance(bs, PhononBandStructureSymmLine)

    def test_get_charge_density_data(self, mpr):
        task_ids = mpr.get_charge_density_calculation_ids_from_material_id("mp-149")
        assert len(task_ids) > 0

        # TODO: Put back in after task data update
        # vasp_calc_details = mpr.get_charge_density_calculation_details(task_ids[0])
        # assert isinstance(vasp_calc_details.incar, Incar)

        chgcar = mpr.get_charge_density_from_calculation_id(task_ids[0]["task_id"])
        assert isinstance(chgcar, Chgcar)
