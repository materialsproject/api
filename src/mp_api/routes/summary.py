from collections import defaultdict
from typing import List, Optional, Tuple, Union

from emmet.core.mpid import MPID
from emmet.core.summary import HasProps, SummaryDoc
from emmet.core.symmetry import CrystalSystem
from mp_api.core.client import BaseRester
from mp_api.core.utils import validate_ids
from pymatgen.analysis.magnetism import Ordering


class SummaryRester(BaseRester[SummaryDoc]):

    suffix = "summary"
    document_model = SummaryDoc  # type: ignore
    primary_key = "material_id"

    def search_summary_docs(
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
        total_magnetization_normalized_formula_units: Optional[Tuple[float, float]] = None,
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
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
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

        query_params = defaultdict(dict)  # type: dict

        min_max_name_dict = {
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "energy_above_hull": "energy_above_hull",
            "uncorrected_energy": "uncorrected_energy_per_atom",
            "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
            "nsites": "nsites",
            "volume": "volume",
            "density": "density",
            "band_gap": "band_gap",
            "efermi": "efermi",
            "total_magnetization": "total_magnetization",
            "total_magnetization_normalized_vol": "total_magnetization_normalized_vol",
            "total_magnetization_normalized_formula_units": "total_magnetization_normalized_formula_units",
            "num_magnetic_sites": "num_magnetic_sites",
            "num_unique_magnetic_sites": "num_unique_magnetic_sites",
            "k_voigt": "k_voigt",
            "k_reuss": "k_reuss",
            "k_vrh": "k_vrh",
            "g_voigt": "g_voigt",
            "g_reuss": "g_reuss",
            "g_vrh": "g_vrh",
            "elastic_anisotropy": "universal_anisotropy",
            "poisson_ratio": "homogeneous_poisson",
            "e_total": "e_total",
            "e_ionic": "e_ionic",
            "e_electronic": "e_electronic",
            "n": "n",
            "piezoelectric_modulus": "e_ij_max",
            "weighted_surface_energy": "weighted_surface_energy",
            "weighted_work_function": "weighted_work_function",
            "surface_energy_anisotropy": "surface_anisotropy",
            "shape_factor": "shape_factor",
        }

        for param, value in locals().items():
            if param in min_max_name_dict and value:
                query_params.update(
                    {
                        "{}_min".format(min_max_name_dict[param]): value[0],
                        "{}_max".format(min_max_name_dict[param]): value[1],
                    }
                )

        if material_ids:
            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if deprecated is not None:
            query_params.update({"deprecated": deprecated})

        if formula:
            query_params.update({"formula": formula})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements is not None:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if possible_species is not None:
            query_params.update({"possible_species": ",".join(possible_species)})

        query_params.update(
            {
                "crystal_system": crystal_system,
                "spacegroup_number": spacegroup_number,
                "spacegroup_symbol": spacegroup_symbol,
            }
        )

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

        if magnetic_ordering:
            query_params.update({"ordering": magnetic_ordering.value})

        if has_reconstructed is not None:
            query_params.update({"has_reconstructed": has_reconstructed})

        if has_props:
            query_params.update({"has_props": ",".join([i.value for i in has_props])})

        if theoretical is not None:
            query_params.update({"theoretical": theoretical})

        if sort_fields:
            query_params.update({"_sort_fields": ",".join([s.strip() for s in sort_fields])})

        query_params = {entry: query_params[entry] for entry in query_params if query_params[entry] is not None}

        return super().search(
            num_chunks=num_chunks, chunk_size=chunk_size, all_fields=all_fields, fields=fields, **query_params
        )
