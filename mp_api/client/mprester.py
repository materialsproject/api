from __future__ import annotations

import itertools
import warnings
from collections import defaultdict
from functools import cache, lru_cache
from typing import TYPE_CHECKING

from emmet.core.electronic_structure import BSPathType
from emmet.core.mpid import MPID, AlphaID
from emmet.core.types.enums import ThermoType
from emmet.core.vasp.calc_types import CalcType
from packaging import version
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.pourbaix_diagram import IonEntry
from pymatgen.core import Composition, Element, Structure
from pymatgen.core.ion import Ion
from pymatgen.entries.computed_entries import ComputedStructureEntry
from pymatgen.io.vasp import Chgcar
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from requests import Session, get

from mp_api.client.core import BaseRester, MPRestError, MPRestWarning
from mp_api.client.core._oxygen_evolution import OxygenEvolution
from mp_api.client.core.settings import MAPI_CLIENT_SETTINGS
from mp_api.client.core.utils import (
    LazyImport,
    load_json,
    validate_api_key,
    validate_endpoint,
    validate_ids,
)
from mp_api.client.routes import GENERIC_RESTERS
from mp_api.client.routes.materials import MATERIALS_RESTERS
from mp_api.client.routes.molecules import MOLECULES_RESTERS

if TYPE_CHECKING:
    from typing import Any, Literal

    from emmet.core.tasks import CoreTaskDoc
    from pymatgen.analysis.phase_diagram import PDEntry
    from pymatgen.entries.computed_entries import ComputedEntry


DEFAULT_THERMOTYPE_CRITERIA = {"thermo_types": ["GGA_GGA+U"]}

RESTER_LAYOUT = {
    "molecules/core": LazyImport(
        "mp_api.client.routes.molecules.molecules.MoleculeRester"
    ),
    "materials/core": LazyImport(
        "mp_api.client.routes.materials.materials.MaterialsRester"
    ),
    **{f"materials/{k}": v for k, v in MATERIALS_RESTERS.items() if k not in {"doi"}},
    **{f"molecules/{k}": v for k, v in MOLECULES_RESTERS.items()},
}
GENERIC_RESTERS = {
    "doi": MATERIALS_RESTERS["doi"],
    **GENERIC_RESTERS,
}

TOP_LEVEL_RESTERS = [
    "molecules/core",
    "materials/core",
    "_general_store",
    "_messages",
    "_user_settings",
    "doi",
]


class MPRester:
    """Access the new Materials Project API."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        notify_db_version: bool = False,
        include_user_agent: bool = True,
        use_document_model: bool = True,
        session: Session | None = None,
        headers: dict | None = None,
        mute_progress_bars: bool = MAPI_CLIENT_SETTINGS.MUTE_PROGRESS_BARS,
        **kwargs,
    ):
        """Initialize the MPRester.

        Arguments:
            api_key (str): A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://next-gen.materialsproject.org/api. If this is None,
                the code will check if there is a "MP_API_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint (str): URL of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other URLs implementing a similar interface.
            notify_db_version (bool): If True, the current MP database version will
                be retrieved and logged locally in the ~/.mprester.log.yaml. If the database
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
            use_document_model: If False, skip the creating the document model and return data
                as a dictionary. This can be simpler to work with but bypasses data validation
                and will not give auto-complete for available fields.
            session: Session object to use. By default (None), the client will create one.
            headers: Custom headers for localhost connections.
            mute_progress_bars:  Whether to mute progress bars.
            **kwargs: access to legacy kwargs that may be in the process of being deprecated
        """
        self.api_key = validate_api_key(api_key)

        self.endpoint = validate_endpoint(endpoint)

        self.headers = headers or {}
        self.session = session or BaseRester._create_session(
            api_key=self.api_key,
            include_user_agent=include_user_agent,
            headers=self.headers,
        )
        self._include_user_agent = include_user_agent
        self.use_document_model = use_document_model
        self.mute_progress_bars = mute_progress_bars
        self._contribs = None

        self._deprecated_attributes = [
            "eos",
            "similarity",
            "tasks",
            "xas",
            "fermi",
            "grain_boundaries",
            "substrates",
            "surface_properties",
            "phonon",
            "elasticity",
            "thermo",
            "dielectric",
            "piezoelectric",
            "magnetism",
            "summary",
            "robocrys",
            "synthesis",
            "insertion_electrodes",
            "electronic_structure",
            "electronic_structure_bandstructure",
            "electronic_structure_dos",
            "oxidation_states",
            "provenance",
            "bonds",
            "alloys",
            "absorption",
            "chemenv",
        ]

        if "monty_decode" in kwargs:
            warnings.warn(
                "Ignoring `monty_decode`, as it is no longer a supported option in `mp_api`."
                "The client by default returns results consistent with `monty_decode=True`.",
                stacklevel=2,
                category=MPRestWarning,
            )

        # Check if emmet version of server is compatible
        emmet_version = MPRester.get_emmet_version(self.endpoint)

        if version.parse(emmet_version.base_version) < version.parse(
            MAPI_CLIENT_SETTINGS.MIN_EMMET_VERSION
        ):
            warnings.warn(
                "The installed version of the mp-api client may not be compatible with the API server. "
                "Please install a previous version if any problems occur."
            )

        if notify_db_version:
            raise NotImplementedError("This has not yet been implemented.")

        # Dynamically set rester attributes.
        # First, materials and molecules top level resters are set.
        # Nested rested are then setup to be loaded dynamically with custom __getattr__ functions.
        self._all_resters = list(RESTER_LAYOUT.values())

        # Instantiate top level core molecules, materials, and DOI resters, as well
        # as the sunder resters to allow the web server to work.
        for rest_name, lazy_rester in (RESTER_LAYOUT | GENERIC_RESTERS).items():
            if rest_name in TOP_LEVEL_RESTERS:
                setattr(
                    self,
                    rest_name.split("/")[0],
                    lazy_rester(
                        api_key=self.api_key,
                        endpoint=self.endpoint,
                        include_user_agent=self._include_user_agent,
                        session=self.session,
                        use_document_model=self.use_document_model,
                        headers=self.headers,
                        mute_progress_bars=self.mute_progress_bars,
                    ),
                )

    @property
    def contribs(self):
        if self._contribs is None:
            try:
                from mpcontribs.client import Client

                self._contribs = Client(
                    self.api_key,  # type: ignore
                    headers=self.headers,
                    session=self.session,
                )

            except ImportError:
                self._contribs = None
                warnings.warn(
                    "mpcontribs-client not installed. "
                    "Install the package to query MPContribs data, construct pourbaix diagrams, "
                    "or to compute cohesive energies: 'pip install mpcontribs-client'"
                )
            except Exception as error:
                self._contribs = None
                warnings.warn(f"Problem loading MPContribs client: {error}")

        return self._contribs

    def __enter__(self):
        """Support for "with" context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for "with" context."""
        self.session.close()

    def __getattr__(self, attr):
        if attr in self._deprecated_attributes:
            warnings.warn(
                f"Accessing {attr} data through MPRester.{attr} is deprecated. "
                f"Please use MPRester.materials.{attr} instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return getattr(super().__getattribute__("materials"), attr)
        else:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {attr!r}"
            )

    def __dir__(self):
        return (
            dir(MPRester)
            + self._deprecated_attributes
            + [r.split("/", 1)[0] for r in TOP_LEVEL_RESTERS if not r.startswith("_")]
        )

    def get_task_ids_associated_with_material_id(
        self, material_id: str, calc_types: list[CalcType] | None = None
    ) -> list[str]:
        """Get Task ID values associated with a specific Material ID.

        Args:
            material_id (str): Material ID
            calc_types ([CalcType]): If specified, will restrict to a certain task type, e.g. [CalcType.GGA_STATIC]

        Returns:
            ([str]): List of Task ID values.
        """
        tasks = self.materials.search(material_ids=material_id, fields=["calc_types"])

        if not tasks:
            return []

        calculations = tasks[0]["calc_types"]

        if calc_types:
            return [
                task
                for task, calc_type in calculations.items()
                if calc_type in calc_types
            ]
        return list(calculations.keys())

    def get_structure_by_material_id(
        self, material_id: str, final: bool = True, conventional_unit_cell: bool = False
    ) -> Structure | list[Structure]:
        """Get a Structure corresponding to a material_id.

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
        """The Materials Project database is periodically updated and has a
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

    @staticmethod
    @cache
    def get_emmet_version(endpoint):
        """Get the latest version emmet-core and emmet-api used in the
        current API service.

        Returns: version as a string
        """
        response = get(url=endpoint + "heartbeat").json()

        error = response.get("error", None)
        if error:
            raise MPRestError(error)

        return version.parse(response["version"])

    def get_material_id_from_task_id(self, task_id: str) -> str | None:
        """Returns the current material_id from a given task_id. The
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

    def get_material_id_references(self, material_id: str) -> list[str]:
        """Returns all references for a material id.

        Args:
            material_id (str): A material id.

        Returns:
            List of BibTeX references ([str])
        """
        docs = self.materials.provenance.search(material_ids=material_id)
        return docs[0]["references"] if docs else []

    def get_material_ids(
        self,
        chemsys_formula: str | list[str],
    ) -> list[MPID]:
        """Get all materials ids for a formula or chemsys.

        Args:
            chemsys_formula (str, List[str]): A chemical system, list of chemical systems
            (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), or single formula (e.g., Fe2O3, Si*).

        Returns:
            List of all materials ids ([MPID])
        """
        inp_k = "formula"
        if isinstance(chemsys_formula, list) or (
            isinstance(chemsys_formula, str) and "-" in chemsys_formula
        ):
            inp_k = "chemsys"

        return sorted(
            doc["material_id"]
            for doc in self.materials.search(
                **{inp_k: chemsys_formula},
                all_fields=False,
                fields=["material_id"],
            )
        )

    def get_structures(
        self, chemsys_formula: str | list[str], final=True
    ) -> list[Structure]:
        """Get a list of Structures corresponding to a chemical system or formula.

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
            docs = self.materials.search(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["structure"],
            )

            return [doc["structure"] for doc in docs]
        else:
            structures = []

            for doc in self.materials.search(
                **input_params,  # type: ignore
                all_fields=False,
                fields=["initial_structures"],
            ):
                structures.extend(doc["initial_structures"])

            return structures

    def find_structure(
        self,
        filename_or_structure: str | Structure,
        ltol: float = MAPI_CLIENT_SETTINGS.LTOL,
        stol: float = MAPI_CLIENT_SETTINGS.STOL,
        angle_tol: float = MAPI_CLIENT_SETTINGS.ANGLE_TOL,
        allow_multiple_results: bool = False,
    ) -> list[str] | str:
        """Finds matching structures from the Materials Project database.

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
        chemsys_formula_mpids: str | list[str],
        compatible_only: bool = True,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
        additional_criteria: dict | None = None,
        **kwargs,
    ) -> list[ComputedStructureEntry]:
        """Get a list of ComputedStructureEntry from a chemical system, or formula, or MPID.

        This returns ComputedStructureEntries with final structures for all thermo types
        represented in the database. Each type corresponds to a different mixing scheme
        (i.e. GGA/GGA+U, GGA/GGA+U/R2SCAN, R2SCAN). By default the thermo_type of the
        entry is also returned.

        Args:
            chemsys_formula_mpids (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]), formula, list of formulas
                (e.g., Fe2O3, Si*, [SiO2, BiFeO3]), Materials Project ID, or list of Materials
                Project IDs (e.g., mp-22526, [mp-22526, mp-149]).
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProject2020Compatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies. This data is obtained from the core "thermo" API endpoint.
            property_data (list): Specify additional properties to include in
                entry.data. If None, only default data is included. Should be a subset of
                input parameters in the 'MPRester.thermo.available_fields' list.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell
            additional_criteria (dict): Any additional criteria to pass. The keys and values should
                correspond to proper function inputs to `MPRester.thermo.search`. For instance,
                if you are only interested in entries on the convex hull, you could pass
                {"energy_above_hull": (0.0, 0.0)} or {"is_stable": True}.
            kwargs: Used here only to gracefully handle deprecated arguments. All kwargs are ignored.

        Returns:
            List ComputedStructureEntry objects.
        """
        if kwargs.pop("inc_structure", None) is not None:
            warnings.warn(
                "The `inc_structure` argument is deprecated as final structures "
                "are always included in all returned ComputedStructureEntry objects."
            )

        if isinstance(chemsys_formula_mpids, str):
            chemsys_formula_mpids = [chemsys_formula_mpids]

        try:
            input_params = {"material_ids": validate_ids(chemsys_formula_mpids)}
        except ValueError:
            if any("-" in entry for entry in chemsys_formula_mpids):
                input_params = {"chemsys": chemsys_formula_mpids}
            else:
                input_params = {"formula": chemsys_formula_mpids}

        if additional_criteria:
            input_params = {**input_params, **additional_criteria}

        entries: set[ComputedStructureEntry] = set()

        fields = (
            ["entries", "thermo_type"]
            if not property_data
            else ["entries", "thermo_type"] + property_data
        )

        docs = self.materials.thermo.search(
            **input_params,  # type: ignore
            all_fields=False,
            fields=fields,
        )

        for doc in docs:
            entry_list = doc["entries"].values()
            for entry in entry_list:
                entry_dict: dict = entry.as_dict() if hasattr(entry, "as_dict") else entry  # type: ignore
                if not compatible_only:
                    entry_dict["correction"] = 0.0
                    entry_dict["energy_adjustments"] = []

                if property_data:
                    entry_dict["data"] = {
                        property: doc[property] for property in property_data
                    }

                if conventional_unit_cell:
                    entry_struct = Structure.from_dict(entry_dict["structure"])
                    s = SpacegroupAnalyzer(
                        entry_struct
                    ).get_conventional_standard_structure()
                    site_ratio = len(s) / len(entry_struct)
                    new_energy = entry_dict["energy"] * site_ratio

                    entry_dict["energy"] = new_energy
                    entry_dict["structure"] = s.as_dict()
                    entry_dict["correction"] = 0.0

                    for element in entry_dict["composition"]:
                        entry_dict["composition"][element] *= site_ratio

                    for correction in entry_dict["energy_adjustments"]:
                        if "n_atoms" in correction:
                            correction["n_atoms"] *= site_ratio

                # Need to store object to permit de-duplication
                entries.add(ComputedStructureEntry.from_dict(entry_dict))

        return list(entries)

    def get_pourbaix_entries(
        self,
        chemsys: str | list[str] | list[ComputedEntry | ComputedStructureEntry],
        solid_compat="MaterialsProject2020Compatibility",
        use_gibbs: Literal[300] | None = None,
    ):
        """A helper function to get all entries necessary to generate
        a Pourbaix diagram from the rest interface.

        Args:
            chemsys (str or [str] or Computed(Structure)Entry):
                Chemical system string comprising element
                symbols separated by dashes, e.g., "Li-Fe-O" or List of element
                symbols, e.g., ["Li", "Fe", "O"].

                Can also be a list of Computed(Structure)Entry objects to allow
                for adding extra calculation data to the Pourbaix Diagram.
                If this is set, the chemsys will be inferred from the entries.
            solid_compat: Compatibility scheme used to pre-process solid DFT energies prior
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

        thermo_types = ["GGA_GGA+U"]
        user_entries: list[ComputedEntry | ComputedStructureEntry] = []
        if isinstance(chemsys, list) and all(
            isinstance(v, ComputedEntry | ComputedStructureEntry) for v in chemsys
        ):
            user_entries = [ce.copy() for ce in chemsys]

            elements = set()
            for entry in user_entries:
                elements.update(entry.elements)
            chemsys = [ele.name for ele in elements]

            user_run_types = set(
                [
                    entry.parameters.get("run_type", "unknown").lower()
                    for entry in user_entries
                ]
            )
            if any("r2scan" in rt for rt in user_run_types):
                thermo_types = ["GGA_GGA+U_R2SCAN"]

        if solid_compat == "MaterialsProjectCompatibility":
            solid_compat = MaterialsProjectCompatibility()
        elif solid_compat == "MaterialsProject2020Compatibility":
            solid_compat = MaterialsProject2020Compatibility()
        elif isinstance(solid_compat, Compatibility):
            pass
        else:
            raise ValueError(
                "Solid compatibility can only be 'MaterialsProjectCompatibility', "
                "'MaterialsProject2020Compatibility', or an instance of a Compatibility class"
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
        ion_ref_entries = (
            self.get_entries_in_chemsys(
                list([str(e) for e in ion_ref_elts] + ["O", "H"]),
                additional_criteria={"thermo_types": thermo_types},
                # use_gibbs=use_gibbs
            )
            + user_entries
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
            ion_ref_entries = compat.process_entries(ion_ref_entries)  # type: ignore
        # TODO - if the commented line above would work, this conditional block
        # could be removed
        if use_gibbs:
            # replace the entries with GibbsComputedStructureEntry
            from pymatgen.entries.computed_entries import GibbsComputedStructureEntry

            ion_ref_entries = GibbsComputedStructureEntry.from_entries(
                ion_ref_entries, temp=use_gibbs
            )
        ion_ref_pd = PhaseDiagram(ion_ref_entries)  # type: ignore

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
                form_e = ion_ref_pd.get_form_energy(entry)  # type: ignore
                new_entry = ComputedEntry(
                    entry.composition, form_e, entry_id=entry.entry_id
                )
                pbx_entry = PourbaixEntry(new_entry)
                pbx_entries.append(pbx_entry)

        return pbx_entries

    @lru_cache
    def get_ion_reference_data(self) -> list[dict]:
        """Download aqueous ion reference data used in the construction of Pourbaix diagrams.

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
                'ΔGᶠRefSolid': {'display': '-561.2 kJ/mol', 'value': -561.2, 'unit': 'kJ/mol'},
                'reference': 'H. E. Barner and R. V. Scheuerman, Handbook of thermochemical data for
                compounds and aqueous species, Wiley, New York (1978)'}}
        """
        return self.contribs.query_contributions(  # type: ignore
            query={"project": "ion_ref_data"},
            fields=["identifier", "formula", "data"],
            paginate=True,
        ).get(
            "data"
        )  # type: ignore

    def get_ion_reference_data_for_chemsys(self, chemsys: str | list) -> list[dict]:
        """Download aqueous ion reference data used in the construction of Pourbaix diagrams.

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
                'ΔGᶠRefSolid': {'display': '-561.2 kJ/mol', 'value': -561.2, 'unit': 'kJ/mol'},
                'reference': 'H. E. Barner and R. V. Scheuerman, Handbook of thermochemical data for
                compounds and aqueous species, Wiley, New York (1978)'}}
        """
        ion_data = self.get_ion_reference_data()

        if isinstance(chemsys, str):
            chemsys = chemsys.split("-")
        return [d for d in ion_data if d["data"]["MajElements"] in chemsys]

    def get_ion_entries(
        self, pd: PhaseDiagram, ion_ref_data: list[dict] | None = None
    ) -> list[IonEntry]:
        """Retrieve IonEntry objects that can be used in the construction of
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
        for _, i_d in enumerate(ion_data):
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

    def get_entry_by_material_id(
        self,
        material_id: str,
        compatible_only: bool = True,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
        **kwargs,
    ):
        """Get all ComputedEntry objects corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProject2020Compatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies. This data is obtained from the core "thermo" API endpoint.
            property_data (list): Specify additional properties to include in
                entry.data. If None, only default data is included. Should be a subset of
                input parameters in the 'MPRester.thermo.available_fields' list.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell
            kwargs : Other kwargs to pass to `get_entries`
        Returns:
            List of ComputedEntry or ComputedStructureEntry object.
        """
        return self.get_entries(
            material_id,
            compatible_only=compatible_only,
            property_data=property_data,
            conventional_unit_cell=conventional_unit_cell,
            **kwargs,
        )

    def get_entries_in_chemsys(
        self,
        elements: str | list[str],
        use_gibbs: int | None = None,
        compatible_only: bool = True,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
        additional_criteria: dict = DEFAULT_THERMOTYPE_CRITERIA,
        **kwargs,
    ):
        """Helper method to get a list of ComputedEntries in a chemical system.
        For example, elements = ["Li", "Fe", "O"] will return a list of all
        entries in the parent Li-Fe-O chemical system, as well as all subsystems
        (i.e., all LixOy, FexOy, LixFey, LixFeyOz, Li, Fe and O phases). Extremely
        useful for creating phase diagrams of entire chemical systems.

        Note that by default this returns mixed GGA/GGA+U entries. For others,
        pass GGA/GGA+U/R2SCAN, or R2SCAN as thermo_types in additional_criteria.

        Args:
            elements (str or [str]): Parent chemical system string comprising element
                symbols separated by dashes, e.g., "Li-Fe-O" or List of element
                symbols, e.g., ["Li", "Fe", "O"].
            use_gibbs: If None (default), DFT energy is returned. If a number, return
                the free energy of formation estimated using a machine learning model
                (see GibbsComputedStructureEntry). The number is the temperature in
                Kelvin at which to estimate the free energy. Must be between 300 K and
                2000 K.
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProject2020Compatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies. This data is obtained from the core "thermo" API endpoint.
            property_data (list): Specify additional properties to include in
                entry.data. If None, only default data is included. Should be a subset of
                input parameters in the 'MPRester.thermo.available_fields' list.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell
            additional_criteria (dict): Any additional criteria to pass. The keys and values should
                correspond to proper function inputs to `MPRester.thermo.search`. For instance,
                if you are only interested in entries on the convex hull, you could pass
                {"energy_above_hull": (0.0, 0.0)} or {"is_stable": True}, or if you are only interested
                in entry data
            kwargs : Other kwargs to pass to `get_entries`
        Returns:
            List of ComputedStructureEntries.
        """
        if isinstance(elements, str):
            elements = elements.split("-")

        elements_set = set(elements)  # remove duplicate elements

        all_chemsyses = [
            "-".join(sorted(els))
            for i in range(len(elements_set))
            for els in itertools.combinations(elements_set, i + 1)
        ]

        entries = []

        entries.extend(
            self.get_entries(
                all_chemsyses,
                compatible_only=compatible_only,
                property_data=property_data,
                conventional_unit_cell=conventional_unit_cell,
                additional_criteria=additional_criteria or DEFAULT_THERMOTYPE_CRITERIA,
                **kwargs,
            )
        )

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
        """Get the band structure pymatgen object associated with a Materials Project ID.

        Arguments:
            material_id (str): Materials Project ID for a material
            path_type (BSPathType): k-point path selection convention
            line_mode (bool): Whether to return data for a line-mode calculation

        Returns:
            bandstructure (Union[BandStructure, BandStructureSymmLine]): BandStructure or BandStructureSymmLine object
        """
        return self.materials.electronic_structure_bandstructure.get_bandstructure_from_material_id(  # type: ignore
            material_id=material_id, path_type=path_type, line_mode=line_mode
        )

    def get_dos_by_material_id(self, material_id: str):
        """Get the complete density of states pymatgen object associated with a Materials Project ID.

        Arguments:
            material_id (str): Materials Project ID for a material

        Returns:
            dos (CompleteDos): CompleteDos object
        """
        return self.materials.electronic_structure_dos.get_dos_from_material_id(
            material_id=material_id
        )  # type: ignore

    def get_phonon_dos_by_material_id(self, material_id: str):
        """Get phonon density of states data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
             CompletePhononDos: A phonon DOS object.

        """
        return self.materials.phonon.get_dos_from_material_id(
            material_id=material_id, phonon_method="dfpt"
        )

    def get_phonon_bandstructure_by_material_id(self, material_id: str):
        """Get phonon dispersion data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            PhononBandStructureSymmLine:  phonon band structure.
        """
        return self.materials.phonon.get_bandstructure_from_material_id(
            material_id=material_id, phonon_method="dfpt"
        )

    def get_wulff_shape(self, material_id: str):
        """Constructs a Wulff shape for a material.

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.


        Returns:
            pymatgen.analysis.wulff.WulffShape
        """
        from pymatgen.analysis.wulff import WulffShape
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

        structure = self.get_structure_by_material_id(material_id)
        doc = self.materials.surface_properties.search(material_ids=material_id)

        if not doc:
            return None

        surfaces: list = doc[0]["surfaces"]

        lattice = (
            SpacegroupAnalyzer(structure).get_conventional_standard_structure().lattice
        )
        miller_energy_map = {}
        for surf in surfaces:
            miller = tuple(surf.miller_index) if surf.miller_index else ()
            # Prefer reconstructed surfaces, which have lower surface energies.
            if (miller not in miller_energy_map) or surf.is_reconstructed:
                miller_energy_map[miller] = surf.surface_energy
        millers, energies = zip(*miller_energy_map.items())
        return WulffShape(lattice, millers, energies)

    def get_charge_density_from_task_id(
        self, task_id: str, inc_task_doc: bool = False
    ) -> Chgcar | tuple[Chgcar, CoreTaskDoc | dict] | None:
        """Get charge density data for a given task_id.

        Arguments:
            task_id (str): A task id
            inc_task_doc (bool): Whether to include the task document in the returned data.

        Returns:
            (Chgcar, (Chgcar, CoreTaskDoc | dict), None): Pymatgen Chgcar object, or tuple with object and CoreTaskDoc
        """
        chgcar = self.materials.tasks._query_open_data(
            bucket="materialsproject-parsed",
            key=f"chgcars/{validate_ids([task_id])[0]}.json.gz",
            decoder=lambda x: load_json(x, deser=True),
        )[0][0]["data"]

        if inc_task_doc:
            task_doc = self.materials.tasks.search(task_ids=task_id)[0]
            return chgcar, task_doc

        return chgcar

    def get_charge_density_from_material_id(
        self, material_id: str, inc_task_doc: bool = False
    ) -> Chgcar | tuple[Chgcar, CoreTaskDoc | dict] | None:
        """Get charge density data for a given Materials Project ID.

        Arguments:
            material_id (str): Material Project ID
            inc_task_doc (bool): Whether to include the task document in the returned data.

        Returns:
            (Chgcar, (Chgcar, CoreTaskDoc | dict), None): Pymatgen Chgcar object,
            or tuple with object and CoreTaskDoc
        """
        # TODO: really we want a recommended task_id for charge densities here
        # this could potentially introduce an ambiguity
        task_ids = self.get_task_ids_associated_with_material_id(
            material_id, calc_types=[CalcType.GGA_Static, CalcType.GGA_U_Static]
        )
        if not task_ids:
            return None

        results: list[CoreTaskDoc] = self.materials.tasks.search(
            task_ids=task_ids, fields=["last_updated", "task_id"]
        )  # type: ignore

        if len(results) == 0:
            return None

        latest_doc = max(results, key=lambda x: x["last_updated"])
        task_id = latest_doc["task_id"]
        return self.get_charge_density_from_task_id(task_id, inc_task_doc)

    def get_download_info(self, material_ids, calc_types=None, file_patterns=None):
        """Get a list of URLs to retrieve raw VASP output files from the NoMaD repository
        Args:
            material_ids (list): list of material identifiers (mp-id's)
            task_types (list): list of task types to include in download (see CalcType Enum class)
            file_patterns (list): list of wildcard file names to include for each task
        Returns:
            a tuple of 1) a dictionary mapping material_ids to task_ids and
            calc_types, and 2) a list of URLs to download zip archives from
            NoMaD repository. Each zip archive will contain a manifest.json with
            metadata info, e.g. the task/external_ids that belong to a directory.
        """
        # task_id's correspond to NoMaD external_id's
        calc_types = (
            [t.value for t in calc_types if isinstance(t, CalcType)]
            if calc_types
            else []
        )

        meta = defaultdict(list)
        for doc in self.materials.search(  # type: ignore
            task_ids=material_ids,
            fields=["calc_types", "deprecated_tasks", "material_id"],
        ):
            for task_id, calc_type in doc["calc_types"].items():
                if calc_types and calc_type not in calc_types:
                    continue
                mp_id = doc["material_id"]
                meta[mp_id].append({"task_id": task_id, "calc_type": calc_type})

        if not meta:
            raise ValueError(f"No tasks found for material id {material_ids}.")

        # return a list of URLs for NoMaD Downloads containing the list of files
        # for every external_id in `task_ids`
        # For reference, please visit https://nomad-lab.eu/prod/rae/api/

        # check if these task ids exist on NOMAD
        prefix = "https://nomad-lab.eu/prod/rae/api/repo/?"
        if file_patterns is not None:
            for file_pattern in file_patterns:
                prefix += f"file_pattern={file_pattern}&"
        prefix += "external_id="

        task_ids = [t["task_id"] for tl in meta.values() for t in tl]
        nomad_exist_task_ids = self._check_get_download_info_url_by_task_id(
            prefix=prefix, task_ids=task_ids
        )
        if len(nomad_exist_task_ids) != len(task_ids):
            self._print_help_message(
                nomad_exist_task_ids, task_ids, file_patterns, calc_types
            )

        # generate download links for those that exist
        prefix = "https://nomad-lab.eu/prod/rae/api/raw/query?"
        if file_patterns is not None:
            for file_pattern in file_patterns:
                prefix += f"file_pattern={file_pattern}&"
        prefix += "external_id="

        urls = [prefix + tids for tids in nomad_exist_task_ids]
        return meta, urls

    def _check_get_download_info_url_by_task_id(self, prefix, task_ids) -> list[str]:
        nomad_exist_task_ids: list[str] = []
        prefix = prefix.replace("/raw/query", "/repo/")
        for task_id in task_ids:
            url = prefix + task_id
            if self._check_nomad_exist(url):
                nomad_exist_task_ids.append(task_id)
        return nomad_exist_task_ids

    @staticmethod
    def _check_nomad_exist(url) -> bool:
        response = get(url=url)
        if response.status_code != 200:
            return False
        content = load_json(response.text)
        if content["pagination"]["total"] == 0:
            return False
        return True

    @staticmethod
    def _print_help_message(nomad_exist_task_ids, task_ids, file_patterns, calc_types):
        non_exist_ids = set(task_ids) - set(nomad_exist_task_ids)
        warnings.warn(
            f"For file patterns [{file_patterns}] and calc_types [{calc_types}], \n"
            f"the following ids are not found on NOMAD [{list(non_exist_ids)}]. \n"
            f"If you need to upload them, please contact Patrick Huck at phuck@lbl.gov"
        )

    def query(*args, **kwargs):
        """The MPRester().query method has been replaced with the MPRester().summary.search method.
        Note this method also no longer supports direct MongoDB-type queries. For more information,
        please see the new documentation.
        """
        raise NotImplementedError(
            """
            The MPRester().query method has been replaced with the MPRester().summary.search method.
            Note this method also no longer supports direct MongoDB-type queries. For more information,
            please see the new documentation.
            """
        )

    def get_cohesive_energy(
        self,
        material_ids: list[MPID | str],
        normalization: Literal["atom", "formula_unit"] = "atom",
    ) -> float | dict[str, float]:
        """Obtain the cohesive energy of the structure(s) corresponding to multiple MPIDs.

        Args:
            material_ids ([MPID | str]) : List of MPIDs to compute cohesive energies.
            normalization (str = "atom" (default) or "formula_unit") :
                Whether to normalize the cohesive energy by the number of atoms (default)
                or by the number of formula units.
                Note that the current default is inconsistent with the legacy API.

        Returns:
            (dict[str,float]) : The cohesive energies (in eV/atom or eV/formula unit) for
            each material, indexed by MPID.
        """
        entry_preference = {
            k: i for i, k in enumerate(["GGA", "GGA_U", "SCAN", "R2SCAN"])
        }
        run_type_to_dfa = {"GGA": "PBE", "GGA_U": "PBE", "R2SCAN": "r2SCAN"}

        energies = {mp_id: {} for mp_id in material_ids}
        entries = self.get_entries(
            material_ids,
            compatible_only=False,
            property_data=None,
            conventional_unit_cell=False,
        )
        for entry in entries:
            entry = {
                "data": entry.data,
                "uncorrected_energy_per_atom": entry.uncorrected_energy_per_atom,
                "composition": entry.composition,
            }

            mp_id = entry["data"]["material_id"]
            if (run_type := entry["data"]["run_type"]) not in energies[mp_id]:
                energies[mp_id][run_type] = {
                    "total_energy_per_atom": float("inf"),
                    "composition": None,
                }

            # Obtain lowest total energy/atom within a given run type
            if (
                entry["uncorrected_energy_per_atom"]
                < energies[mp_id][run_type]["total_energy_per_atom"]
            ):
                energies[mp_id][run_type] = {
                    "total_energy_per_atom": entry["uncorrected_energy_per_atom"],
                    "composition": entry["composition"],
                }

        atomic_energies = self.get_atom_reference_data()

        e_coh_per_atom = {}
        for mp_id, entries in energies.items():
            if not entries:
                e_coh_per_atom[str(mp_id)] = None
                continue
            # take entry from most reliable and available functional
            prefered_func = sorted(list(entries), key=lambda k: entry_preference[k])[-1]
            e_coh_per_atom[str(mp_id)] = self._get_cohesive_energy(
                entries[prefered_func]["composition"],
                entries[prefered_func]["total_energy_per_atom"],
                atomic_energies[run_type_to_dfa.get(prefered_func, prefered_func)],
                normalization=normalization,
            )
        return e_coh_per_atom

    @lru_cache
    def get_atom_reference_data(
        self,
        funcs: tuple[str] = (
            "PBE",
            "SCAN",
            "r2SCAN",
        ),
    ) -> dict[str, dict[str, float]]:
        """Retrieve energies of isolated neutral atoms from MPContribs.

        Args:
            funcs ([str] or None) : list of functionals to retrieve data for.
            Defaults to all available functionals ("PBE", "SCAN", "r2SCAN")
            when set to None.

        Returns:
            (dict[str, dict[str, float]]) : dict containing isolated atom energies,
            indexed first by the functionals in funcs, and second by the atom.
        """
        _atomic_energies = self.contribs.query_contributions(
            query={"project": "isolated_atom_energies"},
            fields=["formula", *[f"data.{dfa}.energy" for dfa in funcs]],
        ).get("data")

        return {
            dfa: {
                entry["formula"]: entry["data"][dfa]["energy"]["value"]
                for entry in _atomic_energies
            }
            for dfa in funcs
        }

    @staticmethod
    def _get_cohesive_energy(
        composition: Composition | dict,
        energy_per_atom: float,
        atomic_energies: dict[str, float],
        normalization: Literal["atom", "formula_unit"] = "atom",
    ) -> float:
        """Obtain the cohesive energy of a given composition and energy.

        Args:
            composition (Composition or dict) : the composition of the structure.
            energy_per_atom (float) : the energy per atom of the structure.
            atomic_energies (dict[str,float]) : a dict containing reference total energies
                of neutral atoms.
            normalization (str = "atom" (default) or "formula_unit") :
                Whether to normalize the cohesive energy by the number of atoms (default)
                or by the number of formula units.

        Returns:
            (float) : the cohesive energy per atom.
        """
        comp = Composition(composition).remove_charges()
        atomic_energy = sum(
            coeff * atomic_energies[str(element)] for element, coeff in comp.items()
        )

        natom = sum(comp.values())
        if normalization == "atom":
            return energy_per_atom - atomic_energy / natom
        elif normalization == "formula_unit":
            num_form_unit = comp.get_reduced_composition_and_factor()[1]
            return (energy_per_atom * natom - atomic_energy) / num_form_unit

    def get_stability(
        self,
        entries: ComputedEntry | ComputedStructureEntry | PDEntry,
        thermo_type: str | ThermoType = ThermoType.GGA_GGA_U,
    ) -> list[dict[str, Any]] | None:
        chemsys = set()
        for entry in entries:
            chemsys.update(entry.composition.elements)
        chemsys_str = "-".join(sorted(str(ele) for ele in chemsys))

        thermo_type = (
            ThermoType(thermo_type) if isinstance(thermo_type, str) else thermo_type
        )

        corrector = None
        if thermo_type == ThermoType.GGA_GGA_U:
            from pymatgen.entries.compatibility import MaterialsProject2020Compatibility

            corrector = MaterialsProject2020Compatibility()

        elif thermo_type == ThermoType.GGA_GGA_U_R2SCAN:
            from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme

            corrector = MaterialsProjectDFTMixingScheme(run_type_2="r2SCAN")

        try:
            pd = self.materials.thermo.get_phase_diagram_from_chemsys(
                chemsys_str, thermo_type=thermo_type
            )
        except MPRestError:
            pd = None

        if not pd:
            warnings.warn(
                f"No phase diagram data available for chemical system {chemsys_str} "
                f"and thermo type {thermo_type}."
            )
            return

        if corrector:
            corrected_entries = corrector.process_entries(entries + pd.all_entries)
        else:
            corrected_entries = [*entries, *pd.all_entries]

        new_pd = PhaseDiagram(corrected_entries)

        return [
            {
                "e_above_hull": new_pd.get_e_above_hull(entry),
                "composition": entry.composition.as_dict(),
                "energy": entry.energy,
                "entry_id": getattr(entry, "entry_id", f"user-entry-{idx}"),
            }
            for idx, entry in enumerate(entries)
        ]

    def get_oxygen_evolution(
        self,
        material_id: str | MPID | AlphaID,
        working_ion: str | Element,
        thermo_type: str | ThermoType = ThermoType.GGA_GGA_U,
    ):
        working_ion = Element(working_ion)
        formatted_mpid = AlphaID(material_id).string
        electrode_docs = self.materials.insertion_electrodes.search(
            battery_ids=[f"{formatted_mpid}_{working_ion.value}"],
            fields=["chemsys", "electrode_object", "framework"],
        )
        if len(electrode_docs) == 0:
            raise ValueError(
                "No available insertion electrode data with MPID = "
                f"{formatted_mpid} and working ion {working_ion.value}"
            )
        if Element.O not in {
            Element(ele) for ele in electrode_docs[0].chemsys.split("-")
        }:
            raise ValueError(
                f"No oxygen in the host framework {electrode_docs[0].framework}"
            )

        inserted_chemsys = "-".join(
            sorted({working_ion.value, *electrode_docs[0].chemsys.split("-")})
        )
        unique_composition = {
            entry.composition
            for entry in electrode_docs[0].electrode_object.get_all_entries()
        }

        phase_diagram = self.materials.thermo.get_phase_diagram_from_chemsys(
            inserted_chemsys,
            thermo_type=ThermoType(thermo_type),
        )
        return OxygenEvolution().get_oxygen_evolution_from_phase_diagram(
            phase_diagram,
            unique_composition,
        )
