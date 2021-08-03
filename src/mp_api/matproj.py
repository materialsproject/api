from os import environ, path
import warnings
from typing import Optional, Tuple, List
from enum import Enum, unique
import itertools

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.surface import get_symmetrically_equivalent_miller_indices
from pymatgen.analysis.magnetism import Ordering
from emmet.core.mpid import MPID
from emmet.core.symmetry import CrystalSystem

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


@unique
class TaskType(Enum):
    """task types available in MP"""

    GGA_OPT = "GGA Structure Optimization"
    GGAU_OPT = "GGA+U Structure Optimization"
    SCAN_OPT = "SCAN Structure Optimization"
    GGA_LINE = "GGA NSCF Line"
    GGAU_LINE = "GGA+U NSCF Line"
    GGA_UNIFORM = "GGA NSCF Uniform"
    GGAU_UNIFORM = "GGA+U NSCF Uniform"
    GGA_STATIC = "GGA Static"
    GGAU_STATIC = "GGA+U Static"
    GGA_STATIC_DIEL = "GGA Static Dielectric"
    GGAU_STATIC_DIEL = "GGA+U Static Dielectric"
    GGA_DEF = "GGA Deformation"
    GGAU_DEF = "GGA+U Deformation"
    LDA_STATIC_DIEL = "LDA Static Dielectric"


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

        self.get_charge_density_from_calculation_id = (
            self.charge_density.get_charge_density_from_calculation_id
        )

        self.get_charge_density_calculation_ids_from_material_id = (
            self.charge_density.get_charge_density_calculation_ids_from_material_id
        )

        self.get_charge_density_calculation_details = (
            self.charge_density.get_charge_density_calculation_details
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
        if len(docs) == 1:  # pragma: no cover
            return str(docs[0].material_id)
        elif len(docs) > 1:  # pragma: no cover
            raise ValueError(
                f"Multiple documents return for {task_id}, this should not happen, please report it!"
            )
        else:  # pragma: no cover
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
        return self.provenance.get_document_by_id(material_id).references

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

    def find_structure(
        self, filename_or_structure, ltol=0.2, stol=0.3, angle_tol=5, limit=1
    ):
        """
        Finds matching structures on the Materials Project site.
        Args:
            filename_or_structure: filename or Structure object
            ltol: fractional length tolerance
            stol: site tolerance
            angle_tol: angle tolerance in degrees
            limit: amount of structure matches to limit to
        Returns:
            A list of matching materials project ids for structure, \
                including normalized rms distances and max distances between paired sites.
        Raises:
            MPRestError
        """

        return self.materials.find_structure(
            filename_or_structure,
            ltol=ltol,
            stol=stol,
            angle_tol=angle_tol,
            limit=limit,
        )

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

    def get_entries_in_chemsys(
        self, elements,
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
        Returns:
            List of ComputedEntries.
        """
        if isinstance(elements, str):
            elements = elements.split("-")

        all_chemsyses = []
        for i in range(len(elements)):
            for els in itertools.combinations(elements, i + 1):
                all_chemsyses.append("-".join(sorted(els)))

        entries = []

        for chemsys in all_chemsyses:
            entries.extend(self.get_entries(chemsys_formula=chemsys))

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
        return self.electronic_structure_dos.get_dos_from_material_id(  # type: ignore
            material_id=material_id
        )

    def get_phonon_dos_by_material_id(self, material_id):
        """
        Get phonon density of states data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
             CompletePhononDos: A phonon DOS object.

        """
        return self.phonon.get_document_by_id(material_id, fields=["ph_dos"]).ph_dos

    def get_phonon_bandstructure_by_material_id(self, material_id):
        """
        Get phonon dispersion data corresponding to a material_id.

        Args:
            material_id (str): Materials Project material_id.

        Returns:
            PhononBandStructureSymmLine:  phonon band structure.
        """
        return self.phonon.get_document_by_id(material_id, fields=["ph_bs"]).ph_bs

    def get_charge_density_by_material_id(self, material_id: str):
        """
        Get charge density data for a given Materials Project ID.

        Arguments:
            material_id (str): Material Project ID

        Returns:
            chgcar (dict): Pymatgen CHGCAR object.
        """

        return self.charge_density.get_charge_density_from_material_id(material_id)  # type: ignore

    def query(
        self,
        material_ids: Optional[List[MPID]] = None,
        chemsys_formula: Optional[str] = None,
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
        equillibrium_reaction_energy: Optional[Tuple[float, float]] = None,
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
        has_props: Optional[List[str]] = None,
        theoretical: Optional[bool] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core data using a variety of search criteria.

        Arguments:
            material_ids (List[MPID]): List of Materials Project IDs to return data for.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            total_energy (Tuple[int,int]): Minimum and maximum corrected total energy in eV/atom to consider.
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
            has_props: (List[str]): The calculated properties available for the material.
            theoretical: (bool): Whether the material is theoretical.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
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
            chemsys_formula=chemsys_formula,
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
            equillibrium_reaction_energy=equillibrium_reaction_energy,
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
            sort_field=sort_field,
            ascending=ascending,
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

    def get_substrates(self, material_id, orient=None):
        """
        Get a substrate list for a material id. The list is in order of
        increasing elastic energy if a elastic tensor is available for
        the material_id.

        Args:
            material_id (str): Materials Project material_id, e.g. 'mp-123'.
            orient (list) : substrate orientation to look for
        Returns:
            list of dicts with substrate matches
        """

        return [
            doc.dict()
            for doc in self.substrates.search_substrates_docs(
                film_id=material_id,
                substrate_orientation=orient,
                sort_field="energy",
                ascending=True,
            )
        ]

    def get_surface_data(self, material_id, miller_index=None):
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

        Returns:
            Surface data for material. Energies are given in SI units (J/m^2).
        """
        doc = self.surface_properties.get_document_by_id(material_id)
        structure = self.get_structure_by_material_id(material_id)

        if miller_index:
            eq_indices = get_symmetrically_equivalent_miller_indices(
                structure, miller_index
            )

            for surface in doc.surfaces:
                if tuple(surface.miller_index) in eq_indices:
                    return surface.dict()
        else:
            return doc.dict()

    def get_wulff_shape(self, material_id):
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
        surfaces = self.get_surface_data(material_id)["surfaces"]
        lattice = (
            SpacegroupAnalyzer(structure).get_conventional_standard_structure().lattice
        )
        miller_energy_map = {}
        for surf in surfaces:
            miller = tuple(surf["miller_index"])
            # Prefer reconstructed surfaces, which have lower surface energies.
            if (miller not in miller_energy_map) or surf["is_reconstructed"]:
                miller_energy_map[miller] = surf["surface_energy"]
        millers, energies = zip(*miller_energy_map.items())
        return WulffShape(lattice, millers, energies)

    def get_gb_data(
        self,
        material_id=None,
        pretty_formula=None,
        chemsys=None,
        sigma=None,
        gb_plane=None,
        rotation_axis=None,
    ):
        """
        Gets grain boundary data for a material.

        Args:
            material_id (str): Materials Project material_id, e.g., 'mp-129'.
            pretty_formula (str): The formula of metals. e.g., 'Fe'
            chemsys (str): Dash delimited elements in material.
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
        return [
            doc.dict()
            for doc in self.grain_boundary.search_grain_boundary_docs(
                material_ids=[material_id] if material_id else None,
                pretty_formula=pretty_formula,
                chemsys=chemsys,
                sigma=sigma,
                gb_plane=gb_plane,
                rotation_axis=rotation_axis,
            )
        ]
