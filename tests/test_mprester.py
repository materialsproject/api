import itertools
import os
import random
import importlib

import numpy as np
import pytest
from emmet.core.tasks import TaskDoc
from emmet.core.thermo import ThermoType
from emmet.core.vasp.calc_types import CalcType
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import IonEntry, PourbaixDiagram, PourbaixEntry
from pymatgen.analysis.wulff import WulffShape
from pymatgen.core import SETTINGS
from pymatgen.core.ion import Ion
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.bandstructure import (
    BandStructure,
    BandStructureSymmLine,
)
from pymatgen.electronic_structure.dos import CompleteDos
from pymatgen.entries.compatibility import (
    MaterialsProjectAqueousCompatibility,
    MaterialsProject2020Compatibility,
)
from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme
from pymatgen.entries.computed_entries import ComputedEntry, GibbsComputedStructureEntry
from pymatgen.io.cif import CifParser
from pymatgen.io.vasp import Chgcar
from pymatgen.phonon.bandstructure import PhononBandStructureSymmLine
from pymatgen.phonon.dos import PhononDos

from mp_api.client import MPRester
from mp_api.client.core.client import MPRestError
from mp_api.client.core.settings import MAPIClientSettings


@pytest.fixture()
def mpr():
    rester = MPRester()
    yield rester
    rester.session.close()


@pytest.mark.skipif(os.getenv("MP_API_KEY", None) is None, reason="No API key found.")
class TestMPRester:
    fake_mp_api_key = "12345678901234567890123456789012"  # 32 chars
    default_endpoint = "https://api.materialsproject.org/"

    def test_get_structure_by_material_id(self, mpr):
        s0 = mpr.get_structure_by_material_id("mp-149")
        assert s0.formula == "Si2"

        s1 = mpr.get_structure_by_material_id("mp-4163", conventional_unit_cell=True)
        assert s1.formula == "Ca12 Ti8 O28"

        s2 = mpr.get_structure_by_material_id("mp-149", final=False)
        assert {s.formula for s in s2} == {"Si2"}

    def test_get_database_version(self, mpr):
        db_version = mpr.get_database_version()
        assert db_version is not None

    def test_get_material_id_from_task_id(self, mpr):
        assert mpr.get_material_id_from_task_id("mp-540081") == "mp-19017"

    def test_get_task_ids_associated_with_material_id(self, mpr):
        results = mpr.get_task_ids_associated_with_material_id(
            "mp-149", calc_types=[CalcType.GGA_Static, CalcType.GGA_U_Static]
        )
        assert len(results) > 0

    def test_get_material_id_references(self, mpr):
        data = mpr.get_material_id_references("mp-123")
        assert len(data) > 5

    def test_get_material_id_doc(self, mpr):
        mp_ids = mpr.get_material_ids("Al2O3")
        random.shuffle(mp_ids)
        doc = mpr.materials.search(material_ids=mp_ids.pop(0))[0]
        assert doc.formula_pretty == "Al2O3"

        mp_ids = mpr.get_material_ids("Al-O")
        random.shuffle(mp_ids)
        doc = mpr.materials.search(material_ids=mp_ids.pop(0))[0]
        assert doc.chemsys == "Al-O"

    def test_get_structures(self, mpr):
        structs = mpr.get_structures("Mn3O4")
        assert len(structs) > 0

        structs = mpr.get_structures("Mn-O", final=False)
        assert len(structs) > 0

    @pytest.mark.skip(reason="Endpoint issues")
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
        bs_uniform = mpr.get_bandstructure_by_material_id("mp-149", line_mode=False)
        assert isinstance(bs_uniform, BandStructure)
        assert not isinstance(bs_uniform, BandStructureSymmLine)

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

        elements = {Element(sym) for sym in syms}
        for e in entries:
            assert isinstance(e, ComputedEntry)
            assert set(e.composition.elements).issubset(elements)

        # Formula
        formula = "SiO2"
        entries = mpr.get_entries(formula)

        for e in entries:
            assert isinstance(e, ComputedEntry)

        # Property data
        formula = "BiFeO3"
        entries = mpr.get_entries(formula, property_data=["energy_above_hull"])

        for e in entries:
            assert e.data.get("energy_above_hull", None) is not None

        # Conventional structure
        entry = mpr.get_entry_by_material_id("mp-22526", conventional_unit_cell=True)[1]

        s = entry.structure
        assert pytest.approx(s.lattice.a) == s.lattice.b
        assert pytest.approx(s.lattice.a) != s.lattice.c
        assert pytest.approx(s.lattice.alpha) == 90
        assert pytest.approx(s.lattice.beta) == 90
        assert pytest.approx(s.lattice.gamma) == 120

        # Ensure energy per atom is same
        prim = mpr.get_entry_by_material_id("mp-22526", conventional_unit_cell=False)[1]

        s = prim.structure
        assert pytest.approx(s.lattice.a) == s.lattice.b
        assert pytest.approx(s.lattice.a, abs=1e-3) == s.lattice.c
        assert pytest.approx(s.lattice.alpha, abs=1e-3) == s.lattice.beta
        assert pytest.approx(s.lattice.alpha, abs=1e-3) == s.lattice.gamma

        # Additional criteria
        entry = mpr.get_entries(
            "mp-149",
            additional_criteria={"energy_above_hull": (0.0, 10)},
            property_data=["energy_above_hull"],
        )[0]

        assert "energy_above_hull" in entry.data

        entries = mpr.get_entries(
            "mp-149",
            additional_criteria={"energy_above_hull": (1, 10)},
            property_data=["energy_above_hull"],
        )

        assert len(entries) == 0

    def test_get_entries_in_chemsys(self, mpr):
        syms = ["Li", "Fe", "O"]
        syms2 = "Li-Fe-O"
        entries = mpr.get_entries_in_chemsys(syms)
        entries2 = mpr.get_entries_in_chemsys(syms2)
        elements = {Element(sym) for sym in syms}
        for e in entries:
            assert isinstance(e, ComputedEntry)
            assert set(e.composition.elements).issubset(elements)

        e1 = {i.entry_id for i in entries}
        e2 = {i.entry_id for i in entries2}
        assert e1 == e2

        gibbs_entries = mpr.get_entries_in_chemsys(syms2, use_gibbs=500)
        for e in gibbs_entries:
            assert isinstance(e, GibbsComputedStructureEntry)

    @pytest.mark.skip(reason="SSL issues")
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
        assert not any(e for e in pbx_entries if "Na" in e.composition)

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

    @pytest.mark.skip(reason="SSL issues")
    def test_get_ion_entries(self, mpr):
        entries = mpr.get_entries_in_chemsys("Ti-O-H")
        pd = PhaseDiagram(entries)
        ion_entry_data = mpr.get_ion_reference_data_for_chemsys("Ti-O-H")
        ion_entries = mpr.get_ion_entries(pd, ion_entry_data)
        assert len(ion_entries) == 5
        assert all([isinstance(i, IonEntry) for i in ion_entries])
        bi_v_entry_data = mpr.get_ion_reference_data_for_chemsys("Bi-V")
        bi_data = mpr.get_ion_reference_data_for_chemsys("Bi")
        v_data = mpr.get_ion_reference_data_for_chemsys("V")
        assert len(bi_v_entry_data) == len(bi_data) + v_data

        # test an incomplete phase diagram
        entries = mpr.get_entries_in_chemsys("Ti-O")
        pd = PhaseDiagram(entries)
        with pytest.raises(ValueError, match="The phase diagram chemical system"):
            mpr.get_ion_entries(pd)

        # test ion energy calculation
        ion_data = mpr.get_ion_reference_data_for_chemsys("S")
        ion_ref_comps = [
            Ion.from_formula(d["data"]["RefSolid"]).composition for d in ion_data
        ]
        ion_ref_elts = set(
            itertools.chain.from_iterable(i.elements for i in ion_ref_comps)
        )
        ion_ref_entries = mpr.get_entries_in_chemsys(
            [*map(str, ion_ref_elts), "O", "H"]
        )
        mpc = MaterialsProjectAqueousCompatibility()
        ion_ref_entries = mpc.process_entries(ion_ref_entries)
        ion_ref_pd = PhaseDiagram(ion_ref_entries)
        ion_entries = mpr.get_ion_entries(ion_ref_pd, ion_ref_data=ion_data)

        # In ion ref data, SO4-2 is -744.27 kJ/mol; ref solid is -1,279.0 kJ/mol
        # so the ion entry should have an energy (-744.27 +1279) = 534.73 kJ/mol
        # or 5.542 eV/f.u. above the energy of Na2SO4
        so4_two_minus = [e for e in ion_entries if e.ion.reduced_formula == "SO4[-2]"][
            0
        ]

        # the ref solid is Na2SO4, ground state mp-4770
        # the rf factor correction is necessary to make sure the composition
        # of the reference solid is normalized to a single formula unit
        ref_solid_entry = [e for e in ion_ref_entries if e.entry_id == "mp-4770"][0]
        rf = ref_solid_entry.composition.get_reduced_composition_and_factor()[1]
        solid_energy = ion_ref_pd.get_form_energy(ref_solid_entry) / rf

        assert np.allclose(so4_two_minus.energy, solid_energy + 5.542, atol=1e-3)

    def test_get_phonon_data_by_material_id(self, mpr):
        bs = mpr.get_phonon_bandstructure_by_material_id("mp-2172")
        assert isinstance(bs, PhononBandStructureSymmLine)

        dos = mpr.get_phonon_dos_by_material_id("mp-2172")
        assert isinstance(dos, PhononDos)

    def test_get_charge_density_from_material_id(self, mpr):
        chgcar = mpr.get_charge_density_from_material_id("mp-149")
        assert isinstance(chgcar, Chgcar)

        chgcar, task_doc = mpr.get_charge_density_from_material_id(
            "mp-149", inc_task_doc=True
        )
        assert isinstance(chgcar, Chgcar)
        assert isinstance(task_doc, TaskDoc)

    def test_get_charge_density_from_task_id(self, mpr):
        chgcar = mpr.get_charge_density_from_task_id("mp-2246557")
        assert isinstance(chgcar, Chgcar)

        chgcar, task_doc = mpr.get_charge_density_from_task_id(
            "mp-2246557", inc_task_doc=True
        )
        assert isinstance(chgcar, Chgcar)
        assert isinstance(task_doc, TaskDoc)

    def test_get_wulff_shape(self, mpr):
        ws = mpr.get_wulff_shape("mp-126")
        assert isinstance(ws, WulffShape)

    def test_large_list(self, mpr):
        mpids = [
            str(doc.material_id)
            for doc in mpr.summary.search(
                chunk_size=1000, num_chunks=10, fields=["material_id"]
            )
        ]
        docs = mpr.summary.search(material_ids=mpids, fields=["material_id"])
        assert len(docs) == 10000

    def test_get_api_key_endpoint_from_env_var(self, monkeypatch: pytest.MonkeyPatch):
        """Ensure the MP_API_KEY and MP_API_ENDPOINT from environment variable
        is retrieved at runtime, not import time.
        """
        # Mock an invalid key and endpoint set before import MPRester
        import mp_api.client

        monkeypatch.setenv("MP_API_ENDPOINT", "INVALID ENDPOINT")
        monkeypatch.setenv("MP_API_KEY", "INVALID KEY")

        importlib.reload(mp_api.client)
        from mp_api.client import MPRester

        monkeypatch.setenv("MP_API_KEY", self.fake_mp_api_key)
        monkeypatch.setenv("MP_API_ENDPOINT", self.default_endpoint)
        assert MPRester().api_key == self.fake_mp_api_key
        assert MPRester().endpoint == self.default_endpoint

    def test_get_api_key_endpoint_from_settings(self, monkeypatch: pytest.MonkeyPatch):
        """Test environment variable "MP_API_KEY" is not set and
        get "PMG_MAPI_KEY" from "SETTINGS".
        """
        monkeypatch.delenv("MP_API_KEY", raising=False)

        # patch pymatgen.core.SETTINGS to contain PMG_MAPI_KEY
        monkeypatch.setitem(SETTINGS, "PMG_MAPI_KEY", self.fake_mp_api_key)

        assert MPRester().api_key == self.fake_mp_api_key

    def test_get_default_api_key_endpoint(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("MP_API_ENDPOINT", raising=False)
        assert MPRester().endpoint == self.default_endpoint

        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(MPRestError, match="No API key found in request"):
            MPRester().get_structure_by_material_id("mp-149")

    def test_invalid_api_key(self, monkeypatch):
        monkeypatch.setenv("MP_API_KEY", "INVALID")
        with pytest.raises(ValueError, match="Keys for the new API are 32 characters"):
            MPRester().get_structure_by_material_id("mp-149")

    def test_get_cohesive_energy_per_atom_utility(self):
        composition = {
            "H": 5,
            "V": 2,
            "P": 3,
        }
        toten_per_atom = -2.0e3
        atomic_energies = {"H": -13.6, "V": -7.2, "P": -0.1}

        by_hand_e_coh = toten_per_atom - sum(
            atomic_energies[k] * v for k, v in composition.items()
        ) / sum(composition.values())

        assert MPRester._get_cohesive_energy(
            composition, toten_per_atom, atomic_energies
        ) == pytest.approx(by_hand_e_coh)

    def test_get_atom_references(self, mpr):
        ae = mpr.get_atom_reference_data(funcs=("PBE",))
        assert list(ae) == ["PBE"]
        assert len(ae["PBE"]) == 89
        assert all(isinstance(v, float) for v in ae["PBE"].values())

        ae = mpr.get_atom_reference_data()
        assert set(ae) == {"PBE", "r2SCAN", "SCAN"}
        assert all(len(entries) == 89 for entries in ae.values())
        assert all(
            isinstance(v, float) for entries in ae.values() for v in entries.values()
        )

    def test_get_cohesive_energy(self):
        ref_e_coh = {
            "atom": {
                "mp-123": -4.029208982500002,
                "mp-149": -4.669184594999999,
                "mp-4163": -6.351402620416668,
                "mp-19017": -4.933409960714286,
            },
            "formula_unit": {
                "mp-123": -4.029208982500002,
                "mp-149": -4.669184594999999,
                "mp-4163": -76.21683144500001,
                "mp-19017": -34.533869725,
            },
        }
        e_coh = {}
        for monty_decode in (True, False):
            with MPRester(
                use_document_model=monty_decode, monty_decode=monty_decode
            ) as _mpr:
                for norm, refs in ref_e_coh.items():
                    _e_coh = _mpr.get_cohesive_energy(list(refs), normalization=norm)
                    if norm == "atom":
                        e_coh["serial" if monty_decode else "noserial"] = _e_coh.copy()

                    # Ensure energies match reference data
                    assert all(v == pytest.approx(refs[k]) for k, v in _e_coh.items())

        # Ensure energies are the same regardless of serialization
        assert all(
            v == pytest.approx(e_coh["noserial"][k]) for k, v in e_coh["serial"].items()
        )

    @pytest.mark.parametrize(
        "chemsys, thermo_type",
        [
            [("Fe", "P"), "GGA_GGA+U"],
            [("Li", "S"), ThermoType.GGA_GGA_U_R2SCAN],
            [("Ni", "Se"), ThermoType.R2SCAN],
            [("Ni", "Kr"), "R2SCAN"],
        ],
    )
    def test_get_stability(self, chemsys, thermo_type):
        """
        This test is adapted from the pymatgen one - the scope is broadened
        to include more diverse chemical environments and thermo types which
        reflect the scope of the current MP database.
        """
        with MPRester() as mpr:
            entries = mpr.get_entries_in_chemsys(
                chemsys, additional_criteria={"thermo_types": [thermo_type]}
            )

            no_compound_entries = all(
                len(entry.composition.elements) == 1 for entry in entries
            )

            modified_entries = [
                ComputedEntry(
                    entry.composition,
                    entry.uncorrected_energy + 0.01,
                    parameters=entry.parameters,
                    entry_id=f"mod_{entry.entry_id}",
                )
                for entry in entries
                if entry.composition.reduced_formula in ["Fe2P", "".join(chemsys)]
            ]

            if len(modified_entries) == 0:
                # create fake entry to get PD retrieval to fail
                modified_entries = [
                    ComputedEntry(
                        "".join(chemsys),
                        np.average([entry.energy for entry in entries]),
                        entry_id=f"hypothetical",
                    )
                ]

            if no_compound_entries:
                with pytest.warns(UserWarning, match="No phase diagram data available"):
                    mpr.get_stability(modified_entries, thermo_type=thermo_type)
                return

            else:
                rester_ehulls = mpr.get_stability(
                    modified_entries, thermo_type=thermo_type
                )

        all_entries = entries + modified_entries

        compat = None
        if thermo_type == "GGA_GGA+U":
            compat = MaterialsProject2020Compatibility()
        elif thermo_type == "GGA_GGA+U_R2SCAN":
            compat = MaterialsProjectDFTMixingScheme(run_type_2="r2SCAN")

        if compat:
            all_entries = compat.process_entries(all_entries)

        pd = PhaseDiagram(all_entries)
        for entry in all_entries:
            if str(entry.entry_id).startswith("mod"):
                for dct in rester_ehulls:
                    if dct["entry_id"] == entry.entry_id:
                        data = dct
                        break
                assert pd.get_e_above_hull(entry) == pytest.approx(data["e_above_hull"])
