from emmet.core.symmetry import CrystalSystem
import pytest
import random
import os
import typing
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
from pymatgen.phonon.dos import PhononDos
from pymatgen.io.vasp import Incar, Chgcar
from pymatgen.analysis.magnetism import Ordering
from pymatgen.analysis.wulff import WulffShape


@pytest.fixture()
def mpr():
    rester = MPRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(
    os.environ.get("MP_API_KEY", None) is None, reason="No API key found."
)
class TestMPRester:
    def test_get_structure_by_material_id(self, mpr):
        s1 = mpr.get_structure_by_material_id("mp-149")
        assert s1.formula == "Si2"

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

    @pytest.mark.xfail  # temp xfail while data is fixed
    def test_get_materials_id_references(self, mpr):
        data = mpr.get_materials_id_references("mp-123")
        assert len(data) > 5

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

    def test_get_entries_in_chemsys(self, mpr):
        syms = ["Li", "Fe", "O"]
        syms2 = "Li-Fe-O"
        entries = mpr.get_entries_in_chemsys(syms)
        entries2 = mpr.get_entries_in_chemsys(syms2)
        elements = set([Element(sym) for sym in syms])
        for e in entries:
            assert isinstance(e, ComputedEntry)
            assert set(e.composition.elements).issubset(elements)

        e1 = set([i.entry_id for i in entries])
        e2 = set([i.entry_id for i in entries2])
        assert e1 == e2

    def test_get_phonon_data_by_material_id(self, mpr):
        bs = mpr.get_phonon_bandstructure_by_material_id("mp-11659")
        assert isinstance(bs, PhononBandStructureSymmLine)

        dos = mpr.get_phonon_dos_by_material_id("mp-11659")
        assert isinstance(dos, PhononDos)

    @pytest.mark.xfail  # temp xfail while data is fixes
    def test_get_charge_density_data(self, mpr):
        task_ids = mpr.get_charge_density_calculation_ids_from_material_id("mp-13")
        assert len(task_ids) > 0

        vasp_calc_details = mpr.get_charge_density_calculation_details(
            task_ids[0]["task_id"]
        )
        assert isinstance(vasp_calc_details.incar, Incar)

        chgcar = mpr.get_charge_density_from_calculation_id(task_ids[0]["task_id"])
        assert isinstance(chgcar, Chgcar)

        chgcar = mpr.get_charge_density_by_material_id("mp-13")
        assert isinstance(chgcar, Chgcar)

    def test_get_substrates(self, mpr):
        substrate_data = mpr.get_substrates("mp-123", [1, 0, 0])
        substrates = [sub_dict["sub_id"] for sub_dict in substrate_data]
        assert "mp-2534" in substrates

    def test_get_surface_data(self, mpr):
        data = mpr.get_surface_data("mp-126")  # Pt
        one_surf = mpr.get_surface_data("mp-129", miller_index=[1, 2, 3])
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

    def test_get_wulff_shape(self, mpr):
        ws = mpr.get_wulff_shape("mp-126")
        assert isinstance(ws, WulffShape)

    @pytest.mark.xfail  # temp xfail while data is fixed
    def test_query(self, mpr):

        excluded_params = [
            "sort_field",
            "ascending",
            "chunk_size",
            "num_chunks",
            "all_fields",
            "fields",
        ]

        alt_name_dict = {
            "material_ids": "material_id",
            "chemsys_formula": "formula_pretty",
            "exclude_elements": "formula_pretty",
            "piezoelectric_modulus": "e_ij_max",
            "crystal_system": "symmetry",
            "spacegroup_symbol": "symmetry",
            "spacegroup_number": "symmetry",
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "uncorrected_energy": "uncorrected_energy_per_atom",
            "equillibrium_reaction_energy": "equillibrium_reaction_energy_per_atom",
            "magnetic_ordering": "ordering",
            "elastic_anisotropy": "universal_anisotropy",
            "poisson_ratio": "homogeneous_poisson",
            "piezoelectric_modulus": "e_ij_max",
            "surface_energy_anisotropy": "surface_anisotropy",
        }  # type: dict

        custom_field_tests = {
            "material_ids": ["mp-149"],
            "chemsys_formula": "SiO2",
            "exclude_elements": ["Si"],
            "crystal_system": CrystalSystem.cubic,
            "spacegroup_number": 38,
            "spacegroup_symbol": "Amm2",
            "magnetic_ordering": Ordering.FM,
            "has_props": ["dielectric"],
            "theoretical": True,
            "has_reconstructed": False,
        }  # type: dict

        search_method = mpr.query

        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and bollean parameter and check if returned
        for entry in param_tuples:
            param = entry[0]
            if param not in excluded_params:
                param_type = entry[1].__args__[0]
                q = None

                if param in custom_field_tests:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: custom_field_tests[param],
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is typing.Tuple[int, int]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is typing.Tuple[float, float]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100.12, 100.12),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type is bool:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: False,
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }

                doc = search_method(**q)[0].dict()

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )
