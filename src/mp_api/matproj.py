from os import environ
from urllib.parse import urljoin

from pymatgen.core import Structure
from pymatgen.entries.compatibility import MaterialsProjectCompatibility

from mp_api.bandstructure.client import BSRester
from mp_api.dos.client import DOSRester
from mp_api.eos.client import EOSRester
from mp_api.materials.client import MaterialsRester
from mp_api.similarity.client import SimilarityRester
from mp_api.tasks.client import TaskRester
from mp_api.xas.client import XASRester
from mp_api.fermi.client import FermiRester
from mp_api.gb.client import GBRester
from mp_api.substrates.client import SubstratesRester
from mp_api.surface_properties.client import SurfacePropertiesRester
from mp_api.wulff.client import WulffRester
from mp_api.phonon.client import PhononRester, PhononImgRester
from mp_api.elasticity.client import ElasticityRester
from mp_api.thermo.client import ThermoRester
from mp_api.dielectric.client import DielectricRester
from mp_api.dois.client import DOIRester
from mp_api.piezo.client import PiezoRester
from mp_api.magnetism.client import MagnetismRester
from mp_api.search.client import SearchRester

_DEPRECATION_WARNING = (
    "MPRester is being modernized. Please use the new method suggested and "
    "read more about these changes at https://docs.materialsproject.org/api. The current "
    "methods will be retained until at least January 2022 for backwards compatibility."
)


# TODO: think about how to migrate from PMG_MAPI_KEY
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
        version=None,
        notify_db_version=True,
        include_user_agent=True,
    ):
        """
        Args:
            api_key (str): A String API key for accessing the MaterialsProject
                REST interface. Please obtain your API key at
                https://www.materialsproject.org/dashboard. If this is None,
                the code will check if there is a "PMG_MAPI_KEY" setting.
                If so, it will use that environment variable. This makes
                easier for heavy users to simply add this environment variable to
                their setups and MPRester can then be called without any arguments.
            endpoint (str): Url of endpoint to access the MaterialsProject REST
                interface. Defaults to the standard Materials Project REST
                address at "https://api.materialsproject.org", but
                can be changed to other urls implementing a similar interface.
            version (Optional[str]): Specify the database snapshot to query.
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
        self.version = version

        self.materials = MaterialsRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.xas = XASRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.similarity = SimilarityRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.eos = EOSRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.tasks = TaskRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.bandstructure = BSRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.dos = DOSRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.fermi = FermiRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.gb = GBRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.substrates = SubstratesRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.surface_properties = SurfacePropertiesRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.wulff = WulffRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.phonon = PhononRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.elasticity = ElasticityRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.thermo = ThermoRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.dielectric = DielectricRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.doi = DOIRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.piezo = PiezoRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )
        self.magnetism = MagnetismRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )

        # TODO: remove this from public client?
        self.phonon_img = PhononImgRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
        )

        self.search = SearchRester(
            api_key=api_key, endpoint=endpoint, include_user_agent=include_user_agent
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
        # TODO: share sessions between different Resters
        for rester in (
            self.materials,
            self.xas,
            self.similarity,
            self.eos,
            self.tasks,
            self.bandstructure,
            self.dos,
            self.fermi,
            self.gb,
            self.substrates,
            self.surface_properties,
            self.wulff,
        ):
            rester.session.close()

    def has(self, mpid):
        # TODO: remove, here until search end-point has a client
        return self.materials.session.get(
            urljoin(self.endpoint, f"search/{mpid}/?fields=has_props")
        ).json()["data"][0]["has_props"]

    ###########################################################################
    # The following methods are retained for backwards compatibility, but will
    # eventually be retired.

    # @deprecated(MPRester.materials.get_structure_by_material_id, _DEPRECATION_WARNING)
    def get_structure_by_material_id(
        self, material_id, final=True, conventional_unit_cell=False
    ) -> Structure:
        """
        Get a Structure corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
            final (bool): Whether to get the final structure, or the initial
                (pre-relaxation) structure. Defaults to True.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell

        Returns:
            Structure object.
        """
        # TODO: decide about `final` and `conventional_unit_cell`
        return self.materials.get_structure_by_material_id(material_id=material_id)

    ###########################################################################
    # The following methods have not been implemented yet.

    # @deprecated(self.materials.get_database_version, _DEPRECATION_WARNING)
    def get_database_version(self):
        """
        The Materials Project database is periodically updated and has a
        database version associated with it. When the database is updated,
        consolidated data (information about "a material") may and does
        change, while calculation data about a specific calculation task
        remains unchanged and available for querying via its task_id.

        The database version is set as a date in the format YYYY-MM-DD,
        where "-DD" may be optional. An additional numerical suffix
        might be added if multiple releases happen on the same day.

        Returns: database version as a string
        """
        raise NotImplementedError

    def get_materials_id_from_task_id(self, task_id):
        """
        Returns a new MP materials id from a task id (which can be
        equivalent to an old materials id)

        Args:
            task_id (str): A task id.

        Returns:
            materials_id (str)
        """
        raise NotImplementedError

    def get_materials_id_references(self, material_id):
        """
        Returns all references for a materials id.

        Args:
            material_id (str): A material id.

        Returns:
            BibTeX (str)
        """
        raise NotImplementedError

    def get_data(self, chemsys_formula_id, data_type="vasp", prop=""):
        """
        Flexible method to get any data using the Materials Project REST
        interface. Generally used by other methods for more specific queries.

        Format of REST return is *always* a list of dict (regardless of the
        number of pieces of data returned. The general format is as follows:

        [{"material_id": material_id, "property_name" : value}, ...]

        This is generally a call to
        https://www.materialsproject.org/rest/v2/materials/vasp/<prop>.
        See https://github.com/materialsproject/mapidoc for details.

        Args:
            chemsys_formula_id (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3) or materials_id (e.g., mp-1234).
            data_type (str): Type of data to return. Currently can either be
                "vasp" or "exp".
            prop (str): Property to be obtained. Should be one of the
                MPRester.supported_task_properties. Leave as empty string for a
                general list of useful properties.
        """
        # TODO: this will likely not stay in current form, e.g. exp key?
        raise NotImplementedError

    def get_materials_ids(self, chemsys_formula):
        """
        Get all materials ids for a formula or chemsys.

        Args:
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3).

        Returns:
            ([str]) List of all materials ids.
        """
        raise NotImplementedError

    def get_doc(self, materials_id):
        """
        Get the entire data document for one materials id. Use this judiciously.

        REST Endpoint: https://www.materialsproject.org/materials/<mp-id>/doc.

        Args:
            materials_id (str): E.g., mp-1143 for Al2O3

        Returns:
            Dict of json document of all data that is displayed on a materials
            details page.
        """
        raise NotImplementedError

    def get_xas_data(self, material_id, absorbing_element):
        """
        Get X-ray absorption spectroscopy data for absorbing element in the
        structure corresponding to a material_id. Only X-ray Absorption Near Edge
        Structure (XANES) for K-edge is supported.

        REST Endpoint:
        https://www.materialsproject.org/materials/<mp-id>/xas/<absorbing_element>.

        Args:
            material_id (str): E.g., mp-1143 for Al2O3
            absorbing_element (str): The absorbing element in the corresponding
                structure. E.g., Al in Al2O3
        """
        raise NotImplementedError

    def get_task_data(self, chemsys_formula_id, prop=""):
        """
        Flexible method to get any data using the Materials Project REST
        interface. Generally used by other methods for more specific queries.
        Unlike the :func:`get_data`_, this method queries the task collection
        for specific run information.

        Format of REST return is *always* a list of dict (regardless of the
        number of pieces of data returned. The general format is as follows:

        [{"material_id": material_id, "property_name" : value}, ...]

        Args:
            chemsys_formula_id (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3) or materials_id (e.g., mp-1234).
            prop (str): Property to be obtained. Should be one of the
                MPRester.supported_properties. Leave as empty string for a
                general list of useful properties.
        """
        raise NotImplementedError

    def get_structures(self, chemsys_formula_id, final=True):
        """
        Get a list of Structures corresponding to a chemical system, formula,
        or materials_id.

        Args:
            chemsys_formula_id (str): A chemical system (e.g., Li-Fe-O),
                or formula (e.g., Fe2O3) or materials_id (e.g., mp-1234).
            final (bool): Whether to get the final structure, or the initial
                (pre-relaxation) structure. Defaults to True.

        Returns:
            List of Structure objects.
        """
        raise NotImplementedError

    def find_structure(self, filename_or_structure):
        """
        Finds matching structures on the Materials Project site.

        Args:
            filename_or_structure: filename or Structure object

        Returns:
            A list of matching materials project ids for structure.

        Raises:
            MPRestError
        """
        raise NotImplementedError

    def get_entries(
        self,
        chemsys_formula_id_criteria,
        compatible_only=True,
        inc_structure=None,
        property_data=None,
        conventional_unit_cell=False,
        sort_by_e_above_hull=False,
    ):
        """
        Get a list of ComputedEntries or ComputedStructureEntries corresponding
        to a chemical system, formula, or materials_id or full criteria.

        Args:
            chemsys_formula_id_criteria (str/dict): A chemical system
                (e.g., Li-Fe-O), or formula (e.g., Fe2O3) or materials_id
                (e.g., mp-1234) or full Mongo-style dict criteria.
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProjectCompatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies.
            inc_structure (str): If None, entries returned are
                ComputedEntries. If inc_structure="initial",
                ComputedStructureEntries with initial structures are returned.
                Otherwise, ComputedStructureEntries with final structures
                are returned.
            property_data (list): Specify additional properties to include in
                entry.data. If None, no data. Should be a subset of
                supported_properties.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell
            sort_by_e_above_hull (bool): Whether to sort the list of entries by
                e_above_hull (will query e_above_hull as a property_data if True).

        Returns:
            List of ComputedEntry or ComputedStructureEntry objects.
        """
        raise NotImplementedError

    def get_pourbaix_entries(
        self, chemsys, solid_compat=MaterialsProjectCompatibility()
    ):
        """
        A helper function to get all entries necessary to generate
        a pourbaix diagram from the rest interface.

        Args:
            chemsys ([str]): A list of elements comprising the chemical
                system, e.g. ['Li', 'Fe']
            solid_compat: Compatiblity scheme used to pre-process solid DFT energies prior to applying aqueous
                energy adjustments. Default: MaterialsProjectCompatibility().
        """
        raise NotImplementedError

    def get_entry_by_material_id(
        self,
        material_id,
        compatible_only=True,
        inc_structure=None,
        property_data=None,
        conventional_unit_cell=False,
    ):
        """
        Get a ComputedEntry corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id (a string,
                e.g., mp-1234).
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProjectCompatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies.
            inc_structure (str): If None, entries returned are
                ComputedEntries. If inc_structure="final",
                ComputedStructureEntries with final structures are returned.
                Otherwise, ComputedStructureEntries with initial structures
                are returned.
            property_data (list): Specify additional properties to include in
                entry.data. If None, no data. Should be a subset of
                supported_properties.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell

        Returns:
            ComputedEntry or ComputedStructureEntry object.
        """
        raise NotImplementedError

    def get_bandstructure_by_material_id(self, material_id, line_mode=True):
        """
        Get a BandStructure corresponding to a material_id.

        REST Endpoint: https://www.materialsproject.org/rest/v2/materials/<mp-id>/vasp/bandstructure or
        https://www.materialsproject.org/rest/v2/materials/<mp-id>/vasp/bandstructure_uniform

        Args:
            material_id (str): Materials Project material_id.
            line_mode (bool): If True, fetch a BandStructureSymmLine object
                (default). If False, return the uniform band structure.

        Returns:
            A BandStructure object.
        """
        raise NotImplementedError

    def get_phonon_dos_by_material_id(self, material_id):
        """
        Get phonon density of states data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            ﻿CompletePhononDos: A phonon DOS object.
        """
        raise NotImplementedError

    def get_phonon_bandstructure_by_material_id(self, material_id):
        """
        Get phonon dispersion data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            PhononBandStructureSymmLine: A phonon band structure.
        """
        raise NotImplementedError

    def get_phonon_ddb_by_material_id(self, material_id):
        """
        Get ABINIT Derivative Data Base (DDB) output for phonon calculations.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            str: ABINIT DDB file as a string.
        """
        raise NotImplementedError

    def get_entries_in_chemsys(
        self,
        elements,
        compatible_only=True,
        inc_structure=None,
        property_data=None,
        conventional_unit_cell=False,
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
            compatible_only (bool): Whether to return only "compatible"
                entries. Compatible entries are entries that have been
                processed using the MaterialsProjectCompatibility class,
                which performs adjustments to allow mixing of GGA and GGA+U
                calculations for more accurate phase diagrams and reaction
                energies.
            inc_structure (str): If None, entries returned are
                ComputedEntries. If inc_structure="final",
                ComputedStructureEntries with final structures are returned.
                Otherwise, ComputedStructureEntries with initial structures
                are returned.
            property_data (list): Specify additional properties to include in
                entry.data. If None, no data. Should be a subset of
                supported_properties.
            conventional_unit_cell (bool): Whether to get the standard
                conventional unit cell

        Returns:
            List of ComputedEntries.

        """
        raise NotImplementedError

    def get_exp_thermo_data(self, formula):
        """
        Get a list of ThermoData objects associated with a formula using the
        Materials Project REST interface.

        Args:
            formula (str): A formula to search for.

        Returns:
            List of ThermoData objects.
        """
        # TODO: MPContribs?
        raise NotImplementedError

    def get_exp_entry(self, formula):
        """
        Returns an ExpEntry object, which is the experimental equivalent of a
        ComputedEntry and can be used for analyses using experimental data.

        Args:
            formula (str): A formula to search for.

        Returns:
            An ExpEntry object.
        """
        # TODO: MPContribs?
        raise NotImplementedError

    def query(
        self,
        criteria,
        properties,
        chunk_size=500,
        max_tries_per_chunk=5,
        mp_decode=True,
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
            criteria (str/dict): Criteria of the query as a string or
                mongo-style dict.

                If string, it supports a powerful but simple string criteria.
                E.g., "Fe2O3" means search for materials with reduced_formula
                Fe2O3. Wild cards are also supported. E.g., "\\*2O" means get
                all materials whose formula can be formed as \\*2O, e.g.,
                Li2O, K2O, etc.

                Other syntax examples:
                mp-1234: Interpreted as a Materials ID.
                Fe2O3 or *2O3: Interpreted as reduced formulas.
                Li-Fe-O or *-Fe-O: Interpreted as chemical systems.

                You can mix and match with spaces, which are interpreted as
                "OR". E.g. "mp-1234 FeO" means query for all compounds with
                reduced formula FeO or with materials_id mp-1234.

                Using a full dict syntax, even more powerful queries can be
                constructed. For example, {"elements":{"$in":["Li",
                "Na", "K"], "$all": ["O"]}, "nelements":2} selects all Li, Na
                and K oxides. {"band_gap": {"$gt": 1}} selects all materials
                with band gaps greater than 1 eV.
            properties (list): Properties to request for as a list. For
                example, ["formula", "formation_energy_per_atom"] returns
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
            [{u'formula': {u'O': 1, u'Li': 2.0}},
            {u'formula': {u'Na': 2.0, u'O': 2.0}},
            {u'formula': {u'K': 1, u'O': 3.0}},
            ...]
        """
        # TODO: discuss
        raise NotImplementedError

    def submit_structures(
        self,
        structures,
        authors,
        projects=None,
        references="",
        remarks=None,
        data=None,
        histories=None,
        created_at=None,
    ):
        """
        Submits a list of structures to the Materials Project as SNL files.
        The argument list mirrors the arguments for the StructureNL object,
        except that a list of structures with the same metadata is used as an
        input.

        .. note::

            As of now, this MP REST feature is open only to a select group of
            users. Opening up submissions to all users is being planned for
            the future.

        Args:
            structures: A list of Structure objects
            authors (list): List of {"name":'', "email":''} dicts,
                *list* of Strings as 'John Doe <johndoe@gmail.com>',
                or a single String with commas separating authors
            projects ([str]): List of Strings ['Project A', 'Project B'].
                This applies to all structures.
            references (str): A String in BibTeX format. Again, this applies to
                all structures.
            remarks ([str]): List of Strings ['Remark A', 'Remark B']
            data ([dict]): A list of free form dict. Namespaced at the root
                level with an underscore, e.g. {"_materialsproject":<custom
                data>}. The length of data should be the same as the list of
                structures if not None.
            histories: List of list of dicts - [[{'name':'', 'url':'',
                'description':{}}], ...] The length of histories should be the
                same as the list of structures if not None.
            created_at (datetime): A datetime object

        Returns:
            A list of inserted submission ids.
        """
        # TODO: discuss
        raise NotImplementedError

    def submit_snl(self, snl):
        """
        Submits a list of StructureNL to the Materials Project site.

        .. note::

            As of now, this MP REST feature is open only to a select group of
            users. Opening up submissions to all users is being planned for
            the future.

        Args:
            snl (StructureNL/[StructureNL]): A single StructureNL, or a list
            of StructureNL objects

        Returns:
            A list of inserted submission ids.

        Raises:
            MPRestError
        """
        # TODO: discuss
        raise NotImplementedError

    def delete_snl(self, snl_ids):
        """
        Delete earlier submitted SNLs.

        .. note::

            As of now, this MP REST feature is open only to a select group of
            users. Opening up submissions to all users is being planned for
            the future.

        Args:
            snl_ids: List of SNL ids.

        Raises:
            MPRestError
        """
        # TODO: discuss
        raise NotImplementedError

    def query_snl(self, criteria):
        """
        Query for submitted SNLs.

        .. note::

            As of now, this MP REST feature is open only to a select group of
            users. Opening up submissions to all users is being planned for
            the future.

        Args:
            criteria (dict): Query criteria.

        Returns:
            A dict, with a list of submitted SNLs in the "response" key.

        Raises:
            MPRestError
        """
        # TODO: discuss
        raise NotImplementedError

    def submit_vasp_directory(
        self,
        rootdir,
        authors,
        projects=None,
        references="",
        remarks=None,
        master_data=None,
        master_history=None,
        created_at=None,
        ncpus=None,
    ):
        """
        Assimilates all vasp run directories beneath a particular
        directory using BorgQueen to obtain structures, and then submits thhem
        to the Materials Project as SNL files. VASP related meta data like
        initial structure and final energies are automatically incorporated.

        .. note::

            As of now, this MP REST feature is open only to a select group of
            users. Opening up submissions to all users is being planned for
            the future.

        Args:
            rootdir (str): Rootdir to start assimilating VASP runs from.
            authors: *List* of {"name":'', "email":''} dicts,
                *list* of Strings as 'John Doe <johndoe@gmail.com>',
                or a single String with commas separating authors. The same
                list of authors should apply to all runs.
            projects ([str]): List of Strings ['Project A', 'Project B'].
                This applies to all structures.
            references (str): A String in BibTeX format. Again, this applies to
                all structures.
            remarks ([str]): List of Strings ['Remark A', 'Remark B']
            master_data (dict): A free form dict. Namespaced at the root
                level with an underscore, e.g. {"_materialsproject":<custom
                data>}. This data is added to all structures detected in the
                directory, in addition to other vasp data on a per structure
                basis.
            master_history: A master history to be added to all entries.
            created_at (datetime): A datetime object
            ncpus (int): Number of cpus to use in using BorgQueen to
                assimilate. Defaults to None, which means serial.
        """
        # TODO: discuss
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

    @staticmethod
    def parse_criteria(criteria_string):
        """
        Parses a powerful and simple string criteria and generates a proper
        mongo syntax criteria.

        Args:
            criteria_string (str): A string representing a search criteria.
                Also supports wild cards. E.g.,
                something like "*2O" gets converted to
                {'pretty_formula': {'$in': [u'B2O', u'Xe2O', u"Li2O", ...]}}

                Other syntax examples:
                    mp-1234: Interpreted as a Materials ID.
                    Fe2O3 or *2O3: Interpreted as reduced formulas.
                    Li-Fe-O or *-Fe-O: Interpreted as chemical systems.

                You can mix and match with spaces, which are interpreted as
                "OR". E.g., "mp-1234 FeO" means query for all compounds with
                reduced formula FeO or with materials_id mp-1234.

        Returns:
            A mongo query dict.
        """
        # TODO: discuss
        raise NotImplementedError
