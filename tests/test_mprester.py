import os
import random
import typing
import numpy as np
import itertools

import pytest
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from emmet.core.tasks import TaskDoc
from emmet.core.vasp.calc_types import CalcType
from mp_api.core.settings import MAPIClientSettings
from mp_api.matproj import MPRester
from pymatgen.analysis.magnetism import Ordering
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import IonEntry, PourbaixDiagram, PourbaixEntry
from pymatgen.analysis.wulff import WulffShape
from pymatgen.core.periodic_table import Element
from pymatgen.core.ion import Ion
from pymatgen.electronic_structure.bandstructure import (
    BandStructure,
    BandStructureSymmLine,
)
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.entries.computed_entries import ComputedEntry, GibbsComputedStructureEntry
from pymatgen.entries.compatibility import MaterialsProjectAqueousCompatibility
from pymatgen.io.cif import CifParser
from pymatgen.io.vasp import Chgcar
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import PhononDos


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
        assert db_version is not None

    def test_get_materials_id_from_task_id(self, mpr):
        assert mpr.get_materials_id_from_task_id("mp-540081") == "mp-19017"

    def test_get_task_ids_associated_with_material_id(self, mpr):
        results = mpr.get_task_ids_associated_with_material_id(
            "mp-149", calc_types=[CalcType.GGA_Static, CalcType.GGA_U_Static]
        )
        assert len(results) > 0

    def test_get_materials_id_references(self, mpr):
        data = mpr.get_materials_id_references("mp-123")
        assert len(data) > 5

    def test_get_materials_ids_doc(self, mpr):
        mpids = mpr.get_materials_ids("Al2O3")
        random.shuffle(mpids)
        doc = mpr.materials.get_data_by_id(mpids.pop(0))
        assert doc.formula_pretty == "Al2O3"

        mpids = mpr.get_materials_ids("Al-O")
        random.shuffle(mpids)
        doc = mpr.materials.get_data_by_id(mpids.pop(0))
        assert doc.chemsys == "Al-O"

    def test_get_structures(self, mpr):
        structs = mpr.get_structures("Mn3O4")
        assert len(structs) > 0

        structs = mpr.get_structures("Mn-O", final=False)
        assert len(structs) > 0

    @pytest.mark.skip(reason="endpoint issues")
    def test_find_structure(self, mpr):
        path = os.path.join(MAPIClientSettings().TEST_FILES, "Si_mp_149.cif")
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

        formula = "SiO2"
        entries = mpr.get_entries(formula)

        for e in entries:
            assert isinstance(e, ComputedEntry)

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

        gibbs_entries = mpr.get_entries_in_chemsys(syms2, use_gibbs=500)
        for e in gibbs_entries:
            assert isinstance(e, GibbsComputedStructureEntry)

    def test_get_pourbaix_entries(self, mpr):
        # test input chemsys as a list of elements
        pbx_entries = mpr.get_pourbaix_entries(["Fe", "Cr"])
        for pbx_entry in pbx_entries:
            assert isinstance(pbx_entry, PourbaixEntry)

        # test input chemsys as a string
        pbx_entries = mpr.get_pourbaix_entries("Fe-Cr")
        for pbx_entry in pbx_entries:
            assert isinstance(pbx_entry, PourbaixEntry)

        # test use_gibbs kwarg
        pbx_entries = mpr.get_pourbaix_entries("Li-O", use_gibbs=300)
        for pbx_entry in pbx_entries:
            assert isinstance(pbx_entry, PourbaixEntry)

        # test solid_compat kwarg
        with pytest.raises(ValueError, match="Solid compatibility can only be"):
            mpr.get_pourbaix_entries("Ti-O", solid_compat=None)

        # test removal of extra elements from reference solids
        # Li-Zn-S has Na in reference solids
        pbx_entries = mpr.get_pourbaix_entries("Li-Zn-S")
        assert not any([e for e in pbx_entries if 'Na' in e.composition])

        # Ensure entries are pourbaix compatible
        PourbaixDiagram(pbx_entries)

        # TODO - old tests copied from pymatgen with specific energy values. Update or delete
        # fe_two_plus = [e for e in pbx_entries if e.entry_id == "ion-0"][0]
        # self.assertAlmostEqual(fe_two_plus.energy, -1.12369, places=3)
        #
        # feo2 = [e for e in pbx_entries if e.entry_id == "mp-25332"][0]
        # self.assertAlmostEqual(feo2.energy, 3.56356, places=3)
        #
        # # Test S, which has Na in reference solids
        # pbx_entries = self.rester.get_pourbaix_entries(["S"])
        # so4_two_minus = pbx_entries[9]
        # self.assertAlmostEqual(so4_two_minus.energy, 0.301511, places=3)


    def test_get_ion_entries(self, mpr):
        entries = mpr.get_entries_in_chemsys("Ti-O-H")
        pd = PhaseDiagram(entries)
        ion_entry_data = mpr.get_ion_reference_data_for_chemsys("Ti-O-H")
        ion_entries = mpr.get_ion_entries(pd, ion_entry_data)
        assert len(ion_entries) == 5
        assert all([isinstance(i, IonEntry) for i in ion_entries])

        # test an incomplete phase diagram
        entries = mpr.get_entries_in_chemsys("Ti-O")
        pd = PhaseDiagram(entries)
        with pytest.raises(ValueError, match="The phase diagram chemical system"):
            mpr.get_ion_entries(pd)

        # test ion energy calculation
        ion_data = mpr.get_ion_reference_data_for_chemsys('S')
        ion_ref_comps = [
            Ion.from_formula(d["data"]["RefSolid"]).composition for d in ion_data
        ]
        ion_ref_elts = set(
            itertools.chain.from_iterable(i.elements for i in ion_ref_comps)
        )
        ion_ref_entries = mpr.get_entries_in_chemsys(
            list([str(e) for e in ion_ref_elts] + ["O", "H"])
        )
        mpc = MaterialsProjectAqueousCompatibility()
        ion_ref_entries = mpc.process_entries(ion_ref_entries)
        ion_ref_pd = PhaseDiagram(ion_ref_entries)
        ion_entries = mpr.get_ion_entries(ion_ref_pd, ion_ref_data=ion_data)

        # In ion ref data, SO4-2 is -744.27 kJ/mol; ref solid is -1,279.0 kJ/mol
        # so the ion entry should have an energy (-744.27 +1279) = 534.73 kJ/mol
        # or 5.542 eV/f.u. above the energy of Na2SO4
        so4_two_minus = [e for e in ion_entries if e.ion.reduced_formula == "SO4[-2]"][0]

        # the ref solid is Na2SO4, ground state mp-4770
        # the rf factor correction is necessary to make sure the composition
        # of the reference solid is normalized to a single formula unit
        ref_solid_entry = [e for e in ion_ref_entries if e.entry_id == 'mp-4770'][0]
        rf = ref_solid_entry.composition.get_reduced_composition_and_factor()[1]
        solid_energy = ion_ref_pd.get_form_energy(ref_solid_entry) / rf

        assert np.allclose(so4_two_minus.energy, solid_energy + 5.542, atol=1e-3)

    def test_get_phonon_data_by_material_id(self, mpr):
        bs = mpr.get_phonon_bandstructure_by_material_id("mp-11659")
        assert isinstance(bs, PhononBandStructureSymmLine)

        dos = mpr.get_phonon_dos_by_material_id("mp-11659")
        assert isinstance(dos, PhononDos)

    @pytest.mark.xfail(reason="SSL issue")
    def test_get_charge_density_data(self, mpr):
        chgcar = mpr.get_charge_density_from_material_id("mp-149")
        assert isinstance(chgcar, Chgcar)

        chgcar, task_doc = mpr.get_charge_density_from_material_id(
            "mp-149", inc_task_doc=True
        )
        assert isinstance(chgcar, Chgcar)
        assert isinstance(task_doc, TaskDoc)

    def test_get_wulff_shape(self, mpr):
        ws = mpr.get_wulff_shape("mp-126")
        assert isinstance(ws, WulffShape)

    def test_query(self, mpr):

        excluded_params = [
            "sort_fields",
            "chunk_size",
            "num_chunks",
            "all_fields",
            "fields",
            "equilibrium_reaction_energy",  # temp until data update
        ]

        alt_name_dict = {
            "material_ids": "material_id",
            "formula": "formula_pretty",
            "exclude_elements": "formula_pretty",
            "piezoelectric_modulus": "e_ij_max",
            "crystal_system": "symmetry",
            "spacegroup_symbol": "symmetry",
            "spacegroup_number": "symmetry",
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "uncorrected_energy": "uncorrected_energy_per_atom",
            "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
            "magnetic_ordering": "ordering",
            "elastic_anisotropy": "universal_anisotropy",
            "poisson_ratio": "homogeneous_poisson",
            "piezoelectric_modulus": "e_ij_max",
            "surface_energy_anisotropy": "surface_anisotropy",
        }  # type: dict

        custom_field_tests = {
            "material_ids": ["mp-149"],
            "formula": "SiO2",
            "chemsys": "Si-O",
            "elements": ["Si", "O"],
            "exclude_elements": ["Si"],
            "possible_species": ["O2-"],
            "crystal_system": CrystalSystem.cubic,
            "spacegroup_number": 38,
            "spacegroup_symbol": "Amm2",
            "has_props": [HasProps.dielectric],
            "theoretical": True,
            "has_reconstructed": False,
            "magnetic_ordering": Ordering.FM,
        }  # type: dict

        search_method = mpr.query

        # Get list of parameters
        param_tuples = list(typing.get_type_hints(search_method).items())

        # Query API for each numeric and boolean parameter and check if returned
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
                elif param_type == typing.Tuple[int, int]:
                    project_field = alt_name_dict.get(param, None)
                    q = {
                        param: (-100, 100),
                        "chunk_size": 1,
                        "num_chunks": 1,
                    }
                elif param_type == typing.Tuple[float, float]:
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

                docs = search_method(**q)

                if len(docs) > 0:
                    doc = docs[0].dict()
                else:
                    raise ValueError("No documents returned")

                assert (
                    doc[project_field if project_field is not None else param]
                    is not None
                )
