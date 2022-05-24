import itertools
import warnings
from functools import lru_cache
from os import environ
from typing import Dict, List, Optional, Tuple, Union

from emmet.core.charge_density import ChgcarDataDoc
from emmet.core.electronic_structure import BSPathType
from emmet.core.mpid import MPID
from emmet.core.settings import EmmetSettings
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from emmet.core.vasp.calc_types import CalcType
from mpcontribs.client import Client
from pymatgen.analysis.magnetism import Ordering
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import IonEntry
from pymatgen.core import Element, Structure, Composition
from pymatgen.core.ion import Ion
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.io.vasp import Chgcar
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from requests import get
from typing_extensions import Literal

from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes import *

_DEPRECATION_WARNING = (
    "MPRester is being modernized. Please use the new method suggested and "
    "read more about these changes at https://docs.materialsproject.org/api. The current "
    "methods will be retained until at least January 2022 for backwards compatibility."
)

_EMMET_SETTINGS = EmmetSettings()

DEFAULT_API_KEY = environ.get("MP_API_KEY", None)
DEFAULT_ENDPOINT = environ.get("MP_API_ENDPOINT", "https://api.materialsproject.org/")


class MPRester:
    """
    Access the new Materials Project API.
    """

    # Type hints for all routes
    # To re-generate this list, use:
    # for rester in MPRester()._all_resters:
    #     print(f"{rester.suffix.replace('/', '_')}: {rester.__class__.__name__}")
    eos: EOSRester
    materials: MaterialsRester
    similarity: SimilarityRester
    tasks: TaskRester
    xas: XASRester
    fermi: FermiRester
    grain_boundary: GrainBoundaryRester
    substrates: SubstratesRester
    surface_properties: SurfacePropertiesRester
    phonon: PhononRester
    elasticity: ElasticityRester
    thermo: ThermoRester
    dielectric: DielectricRester
    doi: DOIRester
    piezoelectric: PiezoRester
    magnetism: MagnetismRester
    summary: SummaryRester
    robocrys: RobocrysRester
    molecules: MoleculesRester
    synthesis: SynthesisRester
    insertion_electrodes: ElectrodeRester
    charge_density: ChargeDensityRester
    electronic_structure: ElectronicStructureRester
    electronic_structure_bandstructure: BandStructureRester
    electronic_structure_dos: DosRester
    oxidation_states: OxidationStatesRester
    provenance: ProvenanceRester
    bonds: BondsRester
    _user_settings: UserSettingsRester
    _general_store: GeneralStoreRester

    def __init__(
        self,
        api_key=DEFAULT_API_KEY,
        endpoint=DEFAULT_ENDPOINT,
        notify_db_version=False,
        include_user_agent=True,
        monty_decode: bool = True,
        use_document_model: bool = True,
    ):
        """
        Args:
            api_key (str): A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://next-gen.materialsproject.org/api. If this is None,
                the code will check if there is a "MP_API_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint (str): Url of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other urls implementing a similar interface.
            notify_db_version (bool): If True, the current MP database version will
                be retrieved and logged locally in the ~/.pmgrc.yaml. If the database
                version changes, you will be notified. The current database version is
                also printed on instantiation. These local logs are not sent to
                materialsproject.org and are not associated with your API key, so be
                aware that a notification may not be presented if you run MPRester
                from multiple computing environments.
            include_user_agent (bool): If True, will include a user agent with the
                HTTP request including information on pymatgen and system version
                making the API request. This helps MP support pymatgen users, and
                is similar to what most web browsers send with each page request.
                Set to False to disable the user agent.
            monty_decode: Decode the data using monty into python objects
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
        """

        if api_key and len(api_key) == 16:
            raise ValueError(
                "Please use a new API key from https://next-gen.materialsproject.org/api "
                "Keys for the new API are 32 characters, whereas keys for the legacy "
                "API are 16 characters."
            )

        self.api_key = api_key
        self.endpoint = endpoint
        self.session = BaseRester._create_session(
            api_key=api_key, include_user_agent=include_user_agent
        )

        try:
            self.contribs = Client(api_key)
        except Exception as error:
            self.contribs = None
            warnings.warn(f"Problem loading MPContribs client: {error}")

        self._all_resters = []

        if notify_db_version:
            raise NotImplementedError("This has not yet been implemented.")

        if not self.endpoint.endswith("/"):
            self.endpoint += "/"

        for cls in BaseRester.__subclasses__():

            rester = cls(
                api_key=api_key,
                endpoint=endpoint,
                include_user_agent=include_user_agent,
                session=self.session,
                monty_decode=monty_decode,
                use_document_model=use_document_model,
            )  # type: BaseRester

            self._all_resters.append(rester)

            setattr(
                self,
                cls.suffix.replace("/", "_"),  # type: ignore
                rester,
            )

    def __enter__(self):
        """
        Support for "with" context.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Support for "with" context.
        """
        self.session.close()

    def get_task_ids_associated_with_material_id(
        self, material_id: str, calc_types: Optional[List[CalcType]] = None
    ) -> List[str]:
        """

        :param material_id:
        :param calc_types: if specified, will restrict to certain task types, e.g. [CalcType.GGA_STATIC]
        :return:
        """
        tasks = self.materials.get_data_by_id(
            material_id, fields=["calc_types"]
        ).calc_types
        if calc_types:
            return [
                task for task, calc_type in tasks.items() if calc_type in calc_types
            ]
        else:
            return list(tasks.keys())

    def get_structure_by_material_id(
        self, material_id: str, final: bool = True, conventional_unit_cell: bool = False
    ) -> Union[Structure, List[Structure]]:
        """
        Get a Structure corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
            final (bool): Whether to get the final structure, or the list of initial
                (pre-relaxation) structures. Defaults to True.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell for the final or list of initial structures.

        Returns:
            Structure object or list of Structure objects.
        """

        structure_data = self.materials.get_structure_by_material_id(
            material_id=material_id, final=final
        )

        if conventional_unit_cell and structure_data:
            if final:
                structure_data = SpacegroupAnalyzer(
                    structure_data
                ).get_conventional_standard_structure()
            else:
                structure_data = [
                    SpacegroupAnalyzer(structure).get_conventional_standard_structure()
                    for structure in structure_data
                ]

        return structure_data

    def get_database_version(self):
        """
        The Materials Project database is periodically updated and has a
        database version associated with it. When the database is updated,
        consolidated data (information about "a material") may and does
        change, while calculation data about a specific calculation task
        remains unchanged and available for querying via its task_id.

        The database version is set as a date in the format YYYY_MM_DD,
        where "_DD" may be optional. An additional numerical suffix
        might be added if multiple releases happen on the same day.

        Returns: database version as a string
        """
        return get(url=self.endpoint + "heartbeat").json()["db_version"]

    def get_materials_id_from_task_id(self, task_id: str) -> Union[str, None]:
        """
        Returns the current material_id from a given task_id. The
        material_id should rarely change, and is usually chosen from
        among the smallest numerical id from the group of task_ids for
        that material. However, in some circumstances it might change,
        and this method is useful for finding the new material_id.

        Args:
            task_id (str): A task id.

        Returns:
            material_id (MPID)
        """
        docs = self.materials.search(task_ids=[task_id], fields=["material_id"])
        if len(docs) == 1:  # pragma: no cover
            return str(docs[0].material_id)  # type: ignore
        elif len(docs) > 1:  # pragma: no cover
            raise ValueError(
                f"Multiple documents return for {task_id}, this should not happen, please report it!"
            )
        else:  # pragma: no cover
            warnings.warn(
                f"No material found containing task {task_id}. Please report it if you suspect a task has gone missing."
            )
            return None

    def get_materials_id_references(self, material_id: str) -> List[str]:
        """
        Returns all references for a materials id.

        Args:
            material_id (str): A material id.

        Returns:
            List of BibTeX references ([str])
        """
        return self.provenance.get_data_by_id(material_id).references

    def get_materials_ids(
        self,
        chemsys_formula: Union[str, List[str]],
    ) -> List[MPID]:
        """
        Get all materials ids for a formula or chemsys.

        Args:
            chemsys_formula (str, List[str]): A chemical system, list of chemical systems
            (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), or single formula (e.g., Fe2O3, Si*).

        Returns:
            List of all materials ids ([MPID])
        """

        if isinstance(chemsys_formula, list) or (
            isinstance(chemsys_formula, str) and "-" in chemsys_formula
        ):
            input_params = {"chemsys": chemsys_formula}
        else:
            input_params = {"formula": chemsys_formula}

        return sorted(
            doc.material_id
            for doc in self.materials.search_material_docs(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["material_id"],
            )
        )

    def get_structures(
        self, chemsys_formula: Union[str, List[str]], final=True
    ) -> List[Structure]:
        """
        Get a list of Structures corresponding to a chemical system or formula.

        Args:
            chemsys_formula (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), or single formula (e.g., Fe2O3, Si*).
            final (bool): Whether to get the final structure, or the list of initial
                (pre-relaxation) structures. Defaults to True.

        Returns:
            List of Structure objects. ([Structure])
        """

        if isinstance(chemsys_formula, list) or (
            isinstance(chemsys_formula, str) and "-" in chemsys_formula
        ):
            input_params = {"chemsys": chemsys_formula}
        else:
            input_params = {"formula": chemsys_formula}

        if final:
            return [
                doc.structure
                for doc in self.materials.search_material_docs(
                    **input_params,  # type: ignore
                    all_fields=False,
                    fields=["structure"],
                )
            ]
        else:
            structures = []

            for doc in self.materials.search_material_docs(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["initial_structures"],
            ):
                structures.extend(doc.initial_structures)

            return structures

    def find_structure(
        self,
        filename_or_structure: Union[str, Structure],
        ltol: float = _EMMET_SETTINGS.LTOL,
        stol: float = _EMMET_SETTINGS.STOL,
        angle_tol: float = _EMMET_SETTINGS.ANGLE_TOL,
        allow_multiple_results: bool = False,
    ) -> Union[List[str], str]:
        """
        Finds matching structures from the Materials Project database.

        Multiple results may be returned of "similar" structures based on
        distance using the pymatgen StructureMatcher algorithm, however only
        a single result should match with the same spacegroup, calculated to the
        default tolerances.

        Args:
            filename_or_structure: filename or Structure object
            ltol: fractional length tolerance
            stol: site tolerance
            angle_tol: angle tolerance in degrees
            allow_multiple_results: changes return type for either
            a single material_id or list of material_ids
        Returns:
            A matching material_id if one is found or list of results if allow_multiple_results
            is True
        Raises:
            MPRestError
        """

        return self.materials.find_structure(
            filename_or_structure,
            ltol=ltol,
            stol=stol,
            angle_tol=angle_tol,
            allow_multiple_results=allow_multiple_results,
        )

    def get_entries(
        self,
        chemsys_formula: Union[str, List[str]],
        sort_by_e_above_hull=False,
    ):
        """
        Get a list of ComputedEntries or ComputedStructureEntries corresponding
        to a chemical system or formula.

        Args:
            chemsys_formula (str): A chemical system, list of chemical systems
            (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), or single formula (e.g., Fe2O3, Si*).
            sort_by_e_above_hull (bool): Whether to sort the list of entries by
                e_above_hull in ascending order.

        Returns:
            List of ComputedEntry or ComputedStructureEntry objects.
        """

        if isinstance(chemsys_formula, list) or (
            isinstance(chemsys_formula, str) and "-" in chemsys_formula
        ):
            input_params = {"chemsys": chemsys_formula}
        else:
            input_params = {"formula": chemsys_formula}

        entries = []

        if sort_by_e_above_hull:

            for doc in self.thermo.search_thermo_docs(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["entries"],
                sort_fields=["energy_above_hull"],
            ):
                entries.extend(list(doc.entries.values()))

            return entries

        else:
            for doc in self.thermo.search_thermo_docs(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["entries"],
            ):
                entries.extend(list(doc.entries.values()))

            return entries

    def get_pourbaix_entries(
        self,
        chemsys: Union[str, List],
        solid_compat="MaterialsProject2020Compatibility",
        use_gibbs: Optional[Literal[300]] = None,
    ):
        """
        A helper function to get all entries necessary to generate
        a Pourbaix diagram from the rest interface.

        Args:
            chemsys (str or [str]): Chemical system string comprising element
                symbols separated by dashes, e.g., "Li-Fe-O" or List of element
                symbols, e.g., ["Li", "Fe", "O"].
            solid_compat: Compatiblity scheme used to pre-process solid DFT energies prior
                to applying aqueous energy adjustments. May be passed as a class (e.g.
                MaterialsProject2020Compatibility) or an instance
                (e.g., MaterialsProject2020Compatibility()). If None, solid DFT energies
                are used as-is. Default: MaterialsProject2020Compatibility
            use_gibbs: Set to 300 (for 300 Kelvin) to use a machine learning model to
                estimate solid free energy from DFT energy (see GibbsComputedStructureEntry).
                This can slightly improve the accuracy of the Pourbaix diagram in some
                cases. Default: None. Note that temperatures other than 300K are not
                permitted here, because MaterialsProjectAqueousCompatibility corrections,
                used in Pourbaix diagram construction, are calculated based on 300 K data.
        """
        # imports are not top-level due to expense
        from pymatgen.analysis.pourbaix_diagram import PourbaixEntry
        from pymatgen.entries.compatibility import (
            Compatibility,
            MaterialsProject2020Compatibility,
            MaterialsProjectAqueousCompatibility,
            MaterialsProjectCompatibility,
        )
        from pymatgen.entries.computed_entries import ComputedEntry

        if solid_compat == "MaterialsProjectCompatibility":
            solid_compat = MaterialsProjectCompatibility()
        elif solid_compat == "MaterialsProject2020Compatibility":
            solid_compat = MaterialsProject2020Compatibility()
        elif isinstance(solid_compat, Compatibility):
            solid_compat = solid_compat
        else:
            raise ValueError(
                "Solid compatibility can only be 'MaterialsProjectCompatibility', "
                "'MaterialsProject2020Compatibility', or an instance of a Compatability class"
            )

        pbx_entries = []

        if isinstance(chemsys, str):
            chemsys = chemsys.split("-")
        # capitalize and sort the elements
        chemsys = sorted(e.capitalize() for e in chemsys)

        # Get ion entries first, because certain ions have reference
        # solids that aren't necessarily in the chemsys (Na2SO4)

        # download the ion reference data from MPContribs
        ion_data = self.get_ion_reference_data_for_chemsys(chemsys)

        # build the PhaseDiagram for get_ion_entries
        ion_ref_comps = [
            Ion.from_formula(d["data"]["RefSolid"]).composition for d in ion_data
        ]
        ion_ref_elts = set(
            itertools.chain.from_iterable(i.elements for i in ion_ref_comps)
        )
        # TODO - would be great if the commented line below would work
        # However for some reason you cannot process GibbsComputedStructureEntry with
        # MaterialsProjectAqueousCompatibility
        ion_ref_entries = self.get_entries_in_chemsys(
            list([str(e) for e in ion_ref_elts] + ["O", "H"]),
            # use_gibbs=use_gibbs
        )

        # suppress the warning about supplying the required energies; they will be calculated from the
        # entries we get from MPRester
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="You did not provide the required O2 and H2O energies.",
            )
            compat = MaterialsProjectAqueousCompatibility(solid_compat=solid_compat)
        # suppress the warning about missing oxidation states
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="Failed to guess oxidation states.*"
            )
            ion_ref_entries = compat.process_entries(ion_ref_entries)
        # TODO - if the commented line above would work, this conditional block
        # could be removed
        if use_gibbs:
            # replace the entries with GibbsComputedStructureEntry
            from pymatgen.entries.computed_entries import GibbsComputedStructureEntry

            ion_ref_entries = GibbsComputedStructureEntry.from_entries(
                ion_ref_entries, temp=use_gibbs
            )
        ion_ref_pd = PhaseDiagram(ion_ref_entries)

        ion_entries = self.get_ion_entries(ion_ref_pd, ion_ref_data=ion_data)
        pbx_entries = [PourbaixEntry(e, f"ion-{n}") for n, e in enumerate(ion_entries)]

        # Construct the solid pourbaix entries from filtered ion_ref entries
        extra_elts = (
            set(ion_ref_elts)
            - {Element(s) for s in chemsys}
            - {Element("H"), Element("O")}
        )
        for entry in ion_ref_entries:
            entry_elts = set(entry.composition.elements)
            # Ensure no OH chemsys or extraneous elements from ion references
            if not (
                entry_elts <= {Element("H"), Element("O")}
                or extra_elts.intersection(entry_elts)
            ):
                # Create new computed entry
                form_e = ion_ref_pd.get_form_energy(entry)
                new_entry = ComputedEntry(
                    entry.composition, form_e, entry_id=entry.entry_id
                )
                pbx_entry = PourbaixEntry(new_entry)
                pbx_entries.append(pbx_entry)

        return pbx_entries

    @lru_cache()
    def get_ion_reference_data(self) -> List[Dict]:
        """
        Download aqueous ion reference data used in the construction of Pourbaix diagrams.

        Use this method to examine the ion reference data and to add additional
        ions if desired. The data returned from this method can be passed to
        get_ion_entries().

        Data are retrieved from the Aqueous Ion Reference Data project
        hosted on MPContribs. Refer to that project and its associated documentation
        for more details about the format and meaning of the data.

        Returns:
            [dict]: Among other data, each record contains 1) the experimental ion  free energy, 2) the
                formula of the reference solid for the ion, and 3) the experimental free energy of the
                reference solid. All energies are given in kJ/mol. An example is given below.

                {'identifier': 'Li[+]',
                'formula': 'Li[+]',
                'data': {'charge': {'display': '1.0', 'value': 1.0, 'unit': ''},
                'ΔGᶠ': {'display': '-293.71 kJ/mol', 'value': -293.71, 'unit': 'kJ/mol'},
                'MajElements': 'Li',
                'RefSolid': 'Li2O',
                'ΔGᶠRefSolid': {'display': '-561.2 kJ/mol',
                    'value': -561.2,
                    'unit': 'kJ/mol'},
                'reference': 'H. E. Barner and R. V. Scheuerman, Handbook of thermochemical data for
                compounds and aqueous species, Wiley, New York (1978)'}}
        """

        ion_data = [
            d
            for d in self.contribs.contributions.get_entries(
                project="ion_ref_data",
                fields=["identifier", "formula", "data"],
                per_page=500,
            ).result()["data"]
        ]

        return ion_data

    def get_ion_reference_data_for_chemsys(
        self, chemsys: Union[str, List]
    ) -> List[Dict]:
        """
        Download aqueous ion reference data used in the construction of Pourbaix diagrams.

        Use this method to examine the ion reference data and to add additional
        ions if desired. The data returned from this method can be passed to
        get_ion_entries().

        Data are retrieved from the Aqueous Ion Reference Data project
        hosted on MPContribs. Refer to that project and its associated documentation
        for more details about the format and meaning of the data.

        Args:
            chemsys (str or [str]): Chemical system string comprising element
                symbols separated by dashes, e.g., "Li-Fe-O" or List of element
                symbols, e.g., ["Li", "Fe", "O"].

        Returns:
            [dict]: Among other data, each record contains 1) the experimental ion  free energy, 2) the
                formula of the reference solid for the ion, and 3) the experimental free energy of the
                reference solid. All energies are given in kJ/mol. An example is given below.

                {'identifier': 'Li[+]',
                'formula': 'Li[+]',
                'data': {'charge': {'display': '1.0', 'value': 1.0, 'unit': ''},
                'ΔGᶠ': {'display': '-293.71 kJ/mol', 'value': -293.71, 'unit': 'kJ/mol'},
                'MajElements': 'Li',
                'RefSolid': 'Li2O',
                'ΔGᶠRefSolid': {'display': '-561.2 kJ/mol',
                    'value': -561.2,
                    'unit': 'kJ/mol'},
                'reference': 'H. E. Barner and R. V. Scheuerman, Handbook of thermochemical data for
                compounds and aqueous species, Wiley, New York (1978)'}}
        """

        ion_data = self.get_ion_reference_data()

        return [d for d in ion_data if d["data"]["MajElements"] in chemsys]

    def get_ion_entries(
        self, pd: PhaseDiagram, ion_ref_data: List[dict] = None
    ) -> List[IonEntry]:
        """
        Retrieve IonEntry objects that can be used in the construction of
        Pourbaix Diagrams. The energies of the IonEntry are calculaterd from
        the solid energies in the provided Phase Diagram to be
        consistent with experimental free energies.

        NOTE! This is an advanced method that assumes detailed understanding
        of how to construct computational Pourbaix Diagrams. If you just want
        to build a Pourbaix Diagram using default settings, use get_pourbaix_entries.

        Args:
            pd: Solid phase diagram on which to construct IonEntry. Note that this
                Phase Diagram MUST include O and H in its chemical system. For example,
                to retrieve IonEntry for Ti, the phase diagram passed here should contain
                materials in the H-O-Ti chemical system. It is also assumed that solid
                energies have already been corrected with MaterialsProjectAqueousCompatibility,
                which is necessary for proper construction of Pourbaix diagrams.
            ion_ref_data: Aqueous ion reference data. If None (default), the data
                are downloaded from the Aqueous Ion Reference Data project hosted
                on MPContribs. To add a custom ionic species, first download
                data using get_ion_reference_data, then add or customize it with
                your additional data, and pass the customized list here.

        Returns:
            [IonEntry]: IonEntry are similar to PDEntry objects. Their energies
                are free energies in eV.
        """
        # determine the chemsys from the phase diagram
        chemsys = "-".join([el.symbol for el in pd.elements])

        # raise ValueError if O and H not in chemsys
        if "O" not in chemsys or "H" not in chemsys:
            raise ValueError(
                "The phase diagram chemical system must contain O and H! Your"
                f" diagram chemical system is {chemsys}."
            )

        if not ion_ref_data:
            ion_data = self.get_ion_reference_data_for_chemsys(chemsys)
        else:
            ion_data = ion_ref_data

        # position the ion energies relative to most stable reference state
        ion_entries = []
        for n, i_d in enumerate(ion_data):
            ion = Ion.from_formula(i_d["formula"])
            refs = [
                e
                for e in pd.all_entries
                if e.composition.reduced_formula == i_d["data"]["RefSolid"]
            ]
            if not refs:
                raise ValueError("Reference solid not contained in entry list")
            stable_ref = sorted(refs, key=lambda x: x.energy_per_atom)[0]
            rf = stable_ref.composition.get_reduced_composition_and_factor()[1]

            # TODO - need a more robust way to convert units
            # use pint here?
            if i_d["data"]["ΔGᶠRefSolid"]["unit"] == "kJ/mol":
                # convert to eV/formula unit
                ref_solid_energy = i_d["data"]["ΔGᶠRefSolid"]["value"] / 96.485
            elif i_d["data"]["ΔGᶠRefSolid"]["unit"] == "MJ/mol":
                # convert to eV/formula unit
                ref_solid_energy = i_d["data"]["ΔGᶠRefSolid"]["value"] / 96485
            else:
                raise ValueError(
                    f"Ion reference solid energy has incorrect unit {i_d['data']['ΔGᶠRefSolid']['unit']}"
                )
            solid_diff = pd.get_form_energy(stable_ref) - ref_solid_energy * rf
            elt = i_d["data"]["MajElements"]
            correction_factor = ion.composition[elt] / stable_ref.composition[elt]
            # TODO - need a more robust way to convert units
            # use pint here?
            if i_d["data"]["ΔGᶠ"]["unit"] == "kJ/mol":
                # convert to eV/formula unit
                ion_free_energy = i_d["data"]["ΔGᶠ"]["value"] / 96.485
            elif i_d["data"]["ΔGᶠ"]["unit"] == "MJ/mol":
                # convert to eV/formula unit
                ion_free_energy = i_d["data"]["ΔGᶠ"]["value"] / 96485
            else:
                raise ValueError(
                    f"Ion free energy has incorrect unit {i_d['data']['ΔGᶠ']['unit']}"
                )
            energy = ion_free_energy + solid_diff * correction_factor
            ion_entries.append(IonEntry(ion, energy))

        return ion_entries

    def get_entry_by_material_id(self, material_id: str):
        """
        Get all ComputedEntry objects corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
        Returns:
            List of ComputedEntry or ComputedStructureEntry object.
        """
        return list(
            self.thermo.get_data_by_id(
                document_id=material_id, fields=["entries"]
            ).entries.values()
        )

    def get_entries_in_chemsys(
        self,
        elements: Union[str, List[str]],
        use_gibbs: Optional[int] = None,
    ):
        """
        Helper method to get a list of ComputedEntries in a chemical system.
        For example, elements = ["Li", "Fe", "O"] will return a list of all
        entries in the Li-Fe-O chemical system, i.e., all LixOy,
        FexOy, LixFey, LixFeyOz, Li, Fe and O phases. Extremely useful for
        creating phase diagrams of entire chemical systems.
        Args:
            elements (str or [str]): Chemical system string comprising element
                symbols separated by dashes, e.g., "Li-Fe-O" or List of element
                symbols, e.g., ["Li", "Fe", "O"].
            use_gibbs: If None (default), DFT energy is returned. If a number, return
                the free energy of formation estimated using a machine learning model
                (see GibbsComputedStructureEntry). The number is the temperature in
                Kelvin at which to estimate the free energy. Must be between 300 K and
                2000 K.
        Returns:
            List of ComputedEntries.
        """
        if isinstance(elements, str):
            elements = elements.split("-")

        all_chemsyses = []
        for i in range(len(elements)):
            for els in itertools.combinations(elements, i + 1):
                all_chemsyses.append("-".join(sorted(els)))

        entries = []  # type: List[ComputedEntry]

        entries.extend(self.get_entries(all_chemsyses))

        if use_gibbs:
            # replace the entries with GibbsComputedStructureEntry
            from pymatgen.entries.computed_entries import GibbsComputedStructureEntry

            entries = GibbsComputedStructureEntry.from_entries(entries, temp=use_gibbs)

        return entries

    def get_bandstructure_by_material_id(
        self,
        material_id: str,
        path_type: BSPathType = BSPathType.setyawan_curtarolo,
        line_mode=True,
    ):
        """
        Get the band structure pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material
            path_type (BSPathType): k-point path selection convention
            line_mode (bool): Whether to return data for a line-mode calculation

        Returns:
            bandstructure (Union[BandStructure, BandStructureSymmLine]): BandStructure or BandStructureSymmLine object
        """
        return self.electronic_structure_bandstructure.get_bandstructure_from_material_id(  # type: ignore
            material_id=material_id, path_type=path_type, line_mode=line_mode
        )

    def get_dos_by_material_id(self, material_id: str):
        """
        Get the complete density of states pymatgen object associated with a Materials Project ID.

        Arguments:
            materials_id (str): Materials Project ID for a material

        Returns:
            dos (CompleteDos): CompleteDos object
        """
        return self.electronic_structure_dos.get_dos_from_material_id(material_id=material_id)  # type: ignore

    def get_phonon_dos_by_material_id(self, material_id: str):
        """
        Get phonon density of states data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
             CompletePhononDos: A phonon DOS object.

        """
        return self.phonon.get_data_by_id(material_id, fields=["ph_dos"]).ph_dos

    def get_phonon_bandstructure_by_material_id(self, material_id: str):
        """
        Get phonon dispersion data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            PhononBandStructureSymmLine:  phonon band structure.
        """
        return self.phonon.get_data_by_id(material_id, fields=["ph_bs"]).ph_bs

    def query(
        self,
        material_ids: Optional[List[MPID]] = None,
        formula: Optional[str] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        possible_species: Optional[List[str]] = None,
        nsites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        crystal_system: Optional[CrystalSystem] = None,
        spacegroup_number: Optional[int] = None,
        spacegroup_symbol: Optional[str] = None,
        deprecated: Optional[bool] = None,
        total_energy: Optional[Tuple[float, float]] = None,
        formation_energy: Optional[Tuple[float, float]] = None,
        energy_above_hull: Optional[Tuple[float, float]] = None,
        equilibrium_reaction_energy: Optional[Tuple[float, float]] = None,
        uncorrected_energy: Optional[Tuple[float, float]] = None,
        is_stable: Optional[bool] = None,
        band_gap: Optional[Tuple[float, float]] = None,
        efermi: Optional[Tuple[float, float]] = None,
        is_gap_direct: Optional[bool] = None,
        is_metal: Optional[bool] = None,
        magnetic_ordering: Optional[Ordering] = None,
        total_magnetization: Optional[Tuple[float, float]] = None,
        total_magnetization_normalized_vol: Optional[Tuple[float, float]] = None,
        total_magnetization_normalized_formula_units: Optional[
            Tuple[float, float]
        ] = None,
        num_magnetic_sites: Optional[Tuple[int, int]] = None,
        num_unique_magnetic_sites: Optional[Tuple[int, int]] = None,
        k_voigt: Optional[Tuple[float, float]] = None,
        k_reuss: Optional[Tuple[float, float]] = None,
        k_vrh: Optional[Tuple[float, float]] = None,
        g_voigt: Optional[Tuple[float, float]] = None,
        g_reuss: Optional[Tuple[float, float]] = None,
        g_vrh: Optional[Tuple[float, float]] = None,
        elastic_anisotropy: Optional[Tuple[float, float]] = None,
        poisson_ratio: Optional[Tuple[float, float]] = None,
        e_total: Optional[Tuple[float, float]] = None,
        e_ionic: Optional[Tuple[float, float]] = None,
        e_electronic: Optional[Tuple[float, float]] = None,
        n: Optional[Tuple[float, float]] = None,
        piezoelectric_modulus: Optional[Tuple[float, float]] = None,
        weighted_surface_energy: Optional[Tuple[float, float]] = None,
        weighted_work_function: Optional[Tuple[float, float]] = None,
        surface_energy_anisotropy: Optional[Tuple[float, float]] = None,
        shape_factor: Optional[Tuple[float, float]] = None,
        has_reconstructed: Optional[bool] = None,
        has_props: Optional[List[HasProps]] = None,
        theoretical: Optional[bool] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core data using a variety of search criteria.

        Arguments:
            material_ids (List[MPID]): List of Materials Project IDs to return data for.
            formula (str): A formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), or single formula (e.g., Fe2O3, Si*).
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            possible_species (List(str)): List of element symbols appended with oxidation states.
                (e.g. Cr2+,O2-)
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            total_energy (Tuple[int,int]): Minimum and maximum corrected total energy in eV/atom to consider.
            equilibrium_reaction_energy (Tuple[float,float]): Minimum and maximum equilibrium reaction energy
                in eV/atom to consider.
            formation_energy (Tuple[int,int]): Minimum and maximum formation energy in eV/atom to consider.
            energy_above_hull (Tuple[int,int]): Minimum and maximum energy above the hull in eV/atom to consider.
            uncorrected_energy (Tuple[int,int]): Minimum and maximum uncorrected total energy in eV/atom to consider.
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            total_magnetization (Tuple[float,float]): Minimum and maximum total magnetization values to consider.
            total_magnetization_normalized_vol (Tuple[float,float]): Minimum and maximum total magnetization values
                normalized by volume to consider.
            total_magnetization_normalized_formula_units (Tuple[float,float]): Minimum and maximum total magnetization
                values normalized by formula units to consider.
            num_magnetic_sites (Tuple[int,int]): Minimum and maximum number of magnetic sites to consider.
            num_unique_magnetic_sites (Tuple[int,int]): Minimum and maximum number of unique magnetic sites
                to consider.
            k_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the bulk modulus.
            k_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the bulk modulus.
            k_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the bulk modulus.
            g_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the shear modulus.
            g_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the shear modulus.
            g_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the shear modulus.
            elastic_anisotropy (Tuple[float,float]): Minimum and maximum value to consider for
                the elastic anisotropy.
            poisson_ratio (Tuple[float,float]): Minimum and maximum value to consider for
                Poisson's ratio.
            e_total (Tuple[float,float]): Minimum and maximum total dielectric constant to consider.
            e_ionic (Tuple[float,float]): Minimum and maximum ionic dielectric constant to consider.
            e_electronic (Tuple[float,float]): Minimum and maximum electronic dielectric constant to consider.
            n (Tuple[float,float]): Minimum and maximum refractive index to consider.
            piezoelectric_modulus (Tuple[float,float]): Minimum and maximum piezoelectric modulus to consider.
            weighted_surface_energy (Tuple[float,float]): Minimum and maximum weighted surface energy in J/m² to
                consider.
            weighted_work_function (Tuple[float,float]): Minimum and maximum weighted work function in eV to consider.
            surface_energy_anisotropy (Tuple[float,float]): Minimum and maximum surface energy anisotropy values to
                consider.
            shape_factor (Tuple[float,float]): Minimum and maximum shape factor values to consider.
            has_reconstructed (bool): Whether the entry has any reconstructed surfaces.
            has_props: (List[HasProps]): The calculated properties available for the material.
            theoretical: (bool): Whether the material is theoretical.
            sort_fields (List[str]): Fields used to sort results. Prefixing with '-' will sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SearchDoc to return data for.
                Default is material_id if all_fields is False.

        Returns:
            ([SummaryDoc]) List of SummaryDoc documents
        """

        return self.summary.search_summary_docs(  # type: ignore
            material_ids=material_ids,
            formula=formula,
            chemsys=chemsys,
            elements=elements,
            exclude_elements=exclude_elements,
            possible_species=possible_species,
            nsites=nsites,
            volume=volume,
            density=density,
            crystal_system=crystal_system,
            spacegroup_number=spacegroup_number,
            spacegroup_symbol=spacegroup_symbol,
            deprecated=deprecated,
            total_energy=total_energy,
            formation_energy=formation_energy,
            energy_above_hull=energy_above_hull,
            equilibrium_reaction_energy=equilibrium_reaction_energy,
            uncorrected_energy=uncorrected_energy,
            is_stable=is_stable,
            band_gap=band_gap,
            efermi=efermi,
            is_gap_direct=is_gap_direct,
            is_metal=is_metal,
            magnetic_ordering=magnetic_ordering,
            total_magnetization=total_magnetization,
            total_magnetization_normalized_vol=total_magnetization_normalized_vol,
            total_magnetization_normalized_formula_units=total_magnetization_normalized_formula_units,
            num_magnetic_sites=num_magnetic_sites,
            num_unique_magnetic_sites=num_unique_magnetic_sites,
            k_voigt=k_voigt,
            k_reuss=k_reuss,
            k_vrh=k_vrh,
            g_voigt=g_voigt,
            g_reuss=g_reuss,
            g_vrh=g_vrh,
            elastic_anisotropy=elastic_anisotropy,
            poisson_ratio=poisson_ratio,
            e_total=e_total,
            e_ionic=e_ionic,
            e_electronic=e_electronic,
            n=n,
            piezoelectric_modulus=piezoelectric_modulus,
            weighted_surface_energy=weighted_surface_energy,
            weighted_work_function=weighted_work_function,
            surface_energy_anisotropy=surface_energy_anisotropy,
            shape_factor=shape_factor,
            has_reconstructed=has_reconstructed,
            has_props=has_props,
            theoretical=theoretical,
            sort_fields=sort_fields,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def submit_structures(self, structures, public_name, public_email):
        """
        Submits a list of structures to the Materials Project.

        Note that public_name and public_email will be used to credit the
        submitter on the Materials Project website.

        Args:
            structures: A list of Structure objects

        Returns:
            ?
        """
        # TODO: call new MPComplete endpoint
        raise NotImplementedError

    def get_wulff_shape(self, material_id: str):
        """
        Constructs a Wulff shape for a material.

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
        Returns:
            pymatgen.analysis.wulff.WulffShape
        """
        from pymatgen.analysis.wulff import WulffShape
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

        structure = self.get_structure_by_material_id(material_id)
        surfaces = surfaces = self.surface_properties.get_data_by_id(
            material_id
        ).surfaces
        lattice = (
            SpacegroupAnalyzer(structure).get_conventional_standard_structure().lattice
        )
        miller_energy_map = {}
        for surf in surfaces:
            miller = tuple(surf.miller_index)
            # Prefer reconstructed surfaces, which have lower surface energies.
            if (miller not in miller_energy_map) or surf.is_reconstructed:
                miller_energy_map[miller] = surf.surface_energy
        millers, energies = zip(*miller_energy_map.items())
        return WulffShape(lattice, millers, energies)

    def get_charge_density_from_material_id(
        self, material_id: str, inc_task_doc: bool = False
    ) -> Optional[Chgcar]:
        """
        Get charge density data for a given Materials Project ID.

        Arguments:
            material_id (str): Material Project ID
            inc_task_doc (bool): Whether to include the task document in the returned data.

        Returns:
            chgcar: Pymatgen Chgcar object.
        """

        # TODO: really we want a recommended task_id for charge densities here
        # this could potentially introduce an ambiguity
        task_ids = self.get_task_ids_associated_with_material_id(
            material_id, calc_types=[CalcType.GGA_Static, CalcType.GGA_U_Static]
        )
        results: List[ChgcarDataDoc] = self.charge_density.search(task_ids=task_ids)  # type: ignore

        if len(results) == 0:
            return None

        latest_doc = max(results, key=lambda x: x.last_updated)

        chgcar = self.charge_density.get_charge_density_from_file_id(latest_doc.fs_id)

        if chgcar is None:
            raise MPRestError(f"No charge density fetched for {material_id}.")

        if inc_task_doc:
            task_doc = self.tasks.get_data_by_id(latest_doc.task_id)
            return chgcar, task_doc

        return chgcar
