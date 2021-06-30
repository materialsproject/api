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

        vasp_calc_details = mpr.get_charge_density_calculation_details(
            task_ids[0]["task_id"]
        )
        assert isinstance(vasp_calc_details.incar, Incar)

        chgcar = mpr.get_charge_density_from_calculation_id(task_ids[0]["task_id"])
        assert isinstance(chgcar, Chgcar)

    def test_get_substrates(self, mpr):
        substrate_data = mpr.get_substrates("mp-123", [1, 0, 0])
        substrates = [sub_dict["sub_id"] for sub_dict in substrate_data]
        assert "mp-2534" in substrates

    def test_get_surface_data(self, mpr):
        data = mpr.get_surface_data("mp-126")  # Pt
        one_surf = mpr.get_surface_data("mp-129", miller_index=[-2, -3, 1])
        assert one_surf["surface_energy"] == pytest.approx(2.99156963)
        assert one_surf["miller_index"] == pytest.approx([3, 2, 1])
        assert "surfaces" in data
        surfaces = data["surfaces"]
        assert len(surfaces) > 0
        surface = surfaces.pop()
        assert "miller_index" in surface
        assert "surface_energy" in surface
        assert "is_reconstructed" in surface
        assert "structure" in surface

    @pytest.mark.xfail  # temporary
    def test_get_gb_data(self, mpr):
        mo_gbs = mpr.get_gb_data(chemsys="Mo")
        assert len(mo_gbs) == 10
        mo_gbs_s5 = mpr.get_gb_data(pretty_formula="Mo", sigma=5)
        assert len(mo_gbs_s5) == 3
        mo_s3_112 = mpr.get_gb_data(
            material_id="mp-129", sigma=3, gb_plane=[1, -1, -2],
        )
        assert len(mo_s3_112) == 1
        gb_f = mo_s3_112[0]["final_structure"]
        assert gb_f.rotation_axis == pytest.approx([1, 1, 0])
        assert gb_f.rotation_angle == pytest.approx(109.47122)
        assert mo_s3_112[0]["gb_energy"] == pytest.approx(0.4796547330588574)
        assert mo_s3_112[0]["w_sep"] == pytest.approx(6.318144)
