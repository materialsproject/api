from os import environ
import warnings

from pymatgen.core import Structure
from pymatgen.entries.compatibility import MaterialsProjectCompatibility
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from mp_api.core.client import BaseRester
from mp_api.routes.electronic_structure.models.core import BSPathType
from mp_api.routes import *

_DEPRECATION_WARNING = (
    "MPRester is being modernized. Please use the new method suggested and "
    "read more about these changes at https://docs.materialsproject.org/api. The current "
    "methods will be retained until at least January 2022 for backwards compatibility."
)


DEFAULT_API_KEY = environ.get("MP_API_KEY", None)
DEFAULT_ENDPOINT = environ.get("MP_API_ENDPOINT", "https://api.materialsproject.org/")


class MPRester:
    """
    Intended as a drop-in replacement for the current MPRester.
    """

    def __init__(
        self,
        api_key=DEFAULT_API_KEY,
        endpoint=DEFAULT_ENDPOINT,
        notify_db_version=True,
        include_user_agent=True,
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
        """

        self.api_key = api_key
        self.endpoint = endpoint
        self.session = BaseRester._create_session(
            api_key=api_key, include_user_agent=include_user_agent
        )

        self._all_resters = []

        for cls in BaseRester.__subclasses__():

            rester = cls(
                api_key=api_key,
                endpoint=endpoint,
                include_user_agent=include_user_agent,
                session=self.session,
            )

            self._all_resters.append(rester)

            setattr(
                self, cls.suffix.replace("/", "_"), rester,
            )

        self.find_structure = self.materials.find_structure

        self.get_bandstructure_by_material_id = (
            self.electronic_structure_bandstructure.get_bandstructure_from_material_id
        )
        self.get_dos_by_material_id = (
            self.electronic_structure_dos.get_dos_from_material_id
        )

        self.get_charge_density_from_calculation_id = (
            self.charge_density.get_charge_density_from_calculation_id
        )

        self.get_charge_density_calculation_details = (
            self.get_charge_density_calculation_details
        )

        self.get_charge_density_calculation_ids_from_material_id = (
            self.charge_density.get_charge_density_calculation_ids_from_material_id
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

    def get_structure_by_material_id(
        self, material_id, final=True, conventional_unit_cell=False
    ) -> Structure:
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

        structure_data = self.materials.get_structure_by_material_id(  # type: ignore
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
        return BaseRester(endpoint=self.endpoint + "/heartbeat")._query_resource()[
            "db_version"
        ]

    def get_materials_id_from_task_id(self, task_id):
        """
        Returns the current material_id from a given task_id. The
        materials_id should rarely change, and is usually chosen from
        among the smallest numerical id from the group of task_ids for
        that material. However, in some circumstances it might change,
        and this method is useful for finding the new material_id.

        Args:
            task_id (str): A task id.

        Returns:
            materials_id (MPID)
        """
        docs = self.materials.search(task_ids=[task_id], fields=["material_id"])
        if len(docs) == 1:
            return docs[0].material_id
        elif len(docs) > 1:
            raise ValueError(
                f"Multiple documents return for {task_id}, this should not happen, please report it!"
            )
        else:
            warnings.warn(
                f"No material found containing task {task_id}. Please report it if you suspect a task has gone missing."
            )
            return None

    def get_materials_id_references(self, material_id):
        """
        Returns all references for a materials id.

        Args:
            material_id (str): A material id.

        Returns:
            BibTeX (str)
        """
        raise NotImplementedError

    def get_materials_ids(self, chemsys_formula):
        """
        Get all materials ids for a formula or chemsys.

        Args:
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3).

        Returns:
            ([MPID]) List of all materials ids.
        """
        return sorted(
            doc.material_id
            for doc in self.materials.search_material_docs(
                chemsys_formula=chemsys_formula,
                all_fields=False,
                fields=["material_id"],
            )
        )

    def get_structures(self, chemsys_formula, final=True):
        """
        Get a list of Structures corresponding to a chemical system, formula,
        or materials_id.

        Args:
            chemsys_formula_id (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3).
            final (bool): Whether to get the final structure, or the list of initial
                (pre-relaxation) structures. Defaults to True.

        Returns:
            List of Structure objects.
        """

        if final:
            return [
                doc.structure
                for doc in self.materials.search_material_docs(
                    chemsys_formula=chemsys_formula,
                    all_fields=False,
                    fields=["structure"],
                )
            ]
        else:
            structures = []

            for doc in self.materials.search_material_docs(
                chemsys_formula=chemsys_formula,
                all_fields=False,
                fields=["initial_structures"],
            ):
                structures.extend(doc.initial_structures)

            return structures

    def get_entries(
        self, chemsys_formula, sort_by_e_above_hull=False,
    ):
        """
        Get a list of ComputedEntries or ComputedStructureEntries corresponding
        to a chemical system or formula.

        Args:
            chemsys_formula (str): A chemical system
                (e.g., Li-Fe-O), or formula (e.g., Fe2O3).
            sort_by_e_above_hull (bool): Whether to sort the list of entries by
                e_above_hull in ascending order.

        Returns:
            List of ComputedEntry or ComputedStructureEntry objects.
        """

        entries = []

        if sort_by_e_above_hull:

            for doc in self.thermo.search_thermo_docs(
                chemsys_formula=chemsys_formula,
                all_fields=False,
                fields=["entries"],
                sort_field="energy_above_hull",
                ascending=True,
            ):
                entries.extend(list(doc.entries.values()))

            return entries

        else:
            for doc in self.thermo.search_thermo_docs(
                chemsys_formula=chemsys_formula, all_fields=False, fields=["entries"],
            ):
                entries.extend(list(doc.entries.values()))

            return entries

    def get_entry_by_material_id(self, material_id):
        """
        Get all ComputedEntry objects corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
        Returns:
            List of ComputedEntry or ComputedStructureEntry object.
        """
        return list(
            self.thermo.get_document_by_id(
                document_id=material_id, fields=["entries"]
            ).entries.values()
        )

    def get_phonon_dos_by_material_id(self, material_id):
        """
        Get phonon density of states data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
             CompletePhononDos: A phonon DOS object.

        """
        raise NotImplementedError

    def get_phonon_bandstructure_by_material_id(self, material_id):
        """
        Get phonon dispersion data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            PhononBandStructureSymmLine:  phonon band structure.
        """
        raise NotImplementedError
        
    def query(
        self,
        criteria,
        properties,
        sort_field=None,
        ascending=None,
        num_chunks=None,
        chunk_size=1000,
        all_fields=True,
        fields=None,
    ):
        r"""

        Performs an advanced query using MongoDB-like syntax for directly
        querying the Materials Project database. This allows one to perform
        queries which are otherwise too cumbersome to perform using the standard
        convenience methods.

        Please consult the Materials API documentation at
        https://github.com/materialsproject/mapidoc, which provides a
        comprehensive explanation of the document schema used in the Materials
        Project (supported criteria and properties) and guidance on how best to
        query for the relevant information you need.

        For queries that request data on more than CHUNK_SIZE materials at once,
        this method will chunk a query by first retrieving a list of material
        IDs that satisfy CRITERIA, and then merging the criteria with a
        restriction to one chunk of materials at a time of size CHUNK_SIZE. You
        can opt out of this behavior by setting CHUNK_SIZE=0. To guard against
        intermittent server errors in the case of many chunks per query,
        possibly-transient server errors will result in re-trying a give chunk
        up to MAX_TRIES_PER_CHUNK times.

        Args:
            criteria (str/dict): Criteria of the query as a dictionary.
                For example, {"elements":{"$in":["Li",
                "Na", "K"], "$all": ["O"]}, "nelements":2} selects all Li, Na
                and K oxides. {"band_gap": {"$gt": 1}} selects all materials
                with band gaps greater than 1 eV.
            properties (list): Properties to request for as a list. For
                example, ["formula_pretty", "formation_energy_per_atom"] returns
                the formula and formation energy per atom.
            chunk_size (int): Number of materials for which to fetch data at a
                time. More data-intensive properties may require smaller chunk
                sizes. Use chunk_size=0 to force no chunking -- this is useful
                when fetching only properties such as 'material_id'.
            max_tries_per_chunk (int): How many times to re-try fetching a given
                chunk when the server gives a 5xx error (e.g. a timeout error).
            mp_decode (bool): Whether to do a decoding to a Pymatgen object
                where possible. In some cases, it might be useful to just get
                the raw python dict, i.e., set to False.

        Returns:
            List of results. E.g.,
            [{u'composition': {u'O': 1, u'Li': 2.0}},
            {u'composition': {u'Na': 2.0, u'O': 2.0}},
            {u'composition': {u'K': 1, u'O': 3.0}},
            ...]
        """
        # TODO: discuss
        raise NotImplementedError

    def submit_structures(
        self,
        structures,
        public_name,
        public_email
    ):
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

    def get_stability(self, entries):
        """
        Returns the stability of all entries.
        """
        # TODO: discuss
        raise NotImplementedError

    def get_cohesive_energy(self, material_id, per_atom=False):
        """
        Gets the cohesive for a material (eV per formula unit). Cohesive energy
            is defined as the difference between the bulk energy and the sum of
            total DFT energy of isolated atoms for atom elements in the bulk.
        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
            per_atom (bool): Whether or not to return cohesive energy per atom
        Returns:
            Cohesive energy (eV).
        """
        raise NotImplementedError

    def get_reaction(self, reactants, products):
        """
        Gets a reaction from the Materials Project.

        Args:
            reactants ([str]): List of formulas
            products ([str]): List of formulas

        Returns:
            rxn
        """
        raise NotImplementedError

    def get_substrates(self, material_id, number=50, orient=None):
        """
        Get a substrate list for a material id. The list is in order of
        increasing elastic energy if a elastic tensor is available for
        the material_id. Otherwise the list is in order of increasing
        matching area.

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
            orient (list) : substrate orientation to look for
            number (int) : number of substrates to return
                n=0 returns all available matches
        Returns:
            list of dicts with substrate matches
        """
        raise NotImplementedError

    def get_all_substrates(self):
        """
        Gets the list of all possible substrates considered in the
        Materials Project substrate database

        Returns:
            list of material_ids corresponding to possible substrates
        """
        raise NotImplementedError

    def get_surface_data(self, material_id, miller_index=None, inc_structures=False):
        """
        Gets surface data for a material. Useful for Wulff shapes.

        Reference for surface data:

        Tran, R., Xu, Z., Radhakrishnan, B., Winston, D., Sun, W., Persson, K.
        A., & Ong, S. P. (2016). Data Descripter: Surface energies of elemental
        crystals. Scientific Data, 3(160080), 1–13.
        http://dx.doi.org/10.1038/sdata.2016.80

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
            miller_index (list of integer): The miller index of the surface.
            e.g., [3, 2, 1]. If miller_index is provided, only one dictionary
            of this specific plane will be returned.
            inc_structures (bool): Include final surface slab structures.
                These are unnecessary for Wulff shape construction.
        Returns:
            Surface data for material. Energies are given in SI units (J/m^2).
        """
        raise NotImplementedError

    def get_wulff_shape(self, material_id):
        """
        Constructs a Wulff shape for a material.

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
        Returns:
            pymatgen.analysis.wulff.WulffShape
        """
        raise NotImplementedError

    def get_gb_data(
        self,
        material_id=None,
        pretty_formula=None,
        chemsys=None,
        sigma=None,
        gb_plane=None,
        rotation_axis=None,
        include_work_of_separation=False,
    ):
        """
        Gets grain boundary data for a material.

        Args:
            material_id (str): Materials Project material_id, e.g., 'mp-129'.
            pretty_formula (str): The formula of metals. e.g., 'Fe'
            sigma(int): The sigma value of a certain type of grain boundary
            gb_plane(list of integer): The Miller index of grain
            boundary plane. e.g., [1, 1, 1]
            rotation_axis(list of integer): The Miller index of rotation
            axis. e.g., [1, 0, 0], [1, 1, 0], and [1, 1, 1]
            Sigma value is determined by the combination of rotation axis and
            rotation angle. The five degrees of freedom (DOF) of one grain boundary
            include: rotation axis (2 DOFs), rotation angle (1 DOF), and grain
            boundary plane (2 DOFs).
            include_work_of_separation (bool): whether to include the work of separation
            (in unit of (J/m^2)). If you want to query the work of separation, please
            specify the material_id.


        Returns:
            A list of grain boundaries that satisfy the query conditions (sigma, gb_plane).
            Energies are given in SI units (J/m^2).
        """
        raise NotImplementedError

    def get_interface_reactions(
        self,
        reactant1,
        reactant2,
        open_el=None,
        relative_mu=None,
        use_hull_energy=False,
    ):
        """
        Gets critical reactions between two reactants.

        Get critical reactions ("kinks" in the mixing ratio where
        reaction products change) between two reactants. See the
        `pymatgen.analysis.interface_reactions` module for more info.

        Args:
            reactant1 (str): Chemical formula for reactant
            reactant2 (str): Chemical formula for reactant
            open_el (str): Element in reservoir available to system
            relative_mu (float): Relative chemical potential of element in
                reservoir with respect to pure substance. Must be non-positive.
            use_hull_energy (bool): Whether to use the convex hull energy for a
            given composition for the reaction energy calculation. If false,
            the energy of the ground state structure will be preferred; if a
            ground state can not be found for a composition, the convex hull
            energy will be used with a warning message.

        Returns:
            list: list of dicts of form {ratio,energy,rxn} where `ratio` is the
                reactant mixing ratio, `energy` is the reaction energy
                in eV/atom, and `rxn` is a
                `pymatgen.analysis.reaction_calculator.Reaction`.

        """
        raise NotImplementedError
