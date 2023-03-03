import warnings
from collections import defaultdict
from typing import List, Optional, Tuple, Union

from emmet.core.mpid import MPID
from emmet.core.molecules.summary import HasProps, SummaryDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class MPculeSummaryRester(BaseRester[SummaryDoc]):

    suffix = "summary"
    document_model = SummaryDoc  # type: ignore
    primary_key = "molecule_id"

    def search(
        self,
        charge: Optional[Tuple[int, int]] = None,
        spin_multiplicity: Optional[Tuple[int, int]] = None,
        nelements: Optional[Tuple[int, int]] = None,
        has_solvent: Optional[Union[str, List[str]]] = None,
        has_level_of_theory: Optional[Union[str, List[str]]] = None,
        has_lot_solvent: Optional[Union[str, List[str]]] = None,
        with_solvent: Optional[str] = None,
        electronic_energy: Optional[Tuple[float, float]] = None,
        ionization_energy: Optional[Tuple[float, float]] = None,
        electron_affinity: Optional[Tuple[float, float]] = None,
        reduction_free_energy: Optional[Tuple[float, float]] = None,
        oxidation_free_energy: Optional[Tuple[float, float]] = None,
        # zero_point_energy: Optional[Tuple[float, float]] = None,
        # total_enthalpy: Optional[Tuple[float, float]] = None,
        # total_entropy: Optional[Tuple[float, float]] = None,
        # translational_enthalpy: Optional[Tuple[float, float]] = None,
        # translational_entropy: Optional[Tuple[float, float]] = None,
        # vibrational_enthalpy: Optional[Tuple[float, float]] = None,
        # vibrational_entropy: Optional[Tuple[float, float]] = None,
        # rotational_enthalpy: Optional[Tuple[float, float]] = None,
        # rotational_entropy: Optional[Tuple[float, float]] = None,
        # free_energy: Optional[Tuple[float, float]] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        deprecated: Optional[bool] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        formula: Optional[Union[str, List[str]]] = None,
        has_props: Optional[List[HasProps]] = None,
        material_ids: Optional[List[MPID]] = None,
        num_elements: Optional[Tuple[int, int]] = None,
        # num_sites: Optional[Tuple[int, int]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core data using a variety of search criteria.

        Arguments:
            charge (Tuple[int, int]): Minimum and maximum charge for the molecule.
            spin_multiplicity (Tuple[int, int]): Minimum and maximum spin for the molecule.
            nelements (Tuple[int, int]): Minimum and maximum number of elements
            has_solvent (str, List[str]): Whether the molecule has properties calculated in
                solvents (e.g., "SOLVENT=THF", ["SOLVENT=WATER", "VACUUM"])
            has_level_of_theory (str, List[str]): Whether the molecule has properties calculated
                using a particular level of theory (e.g. "wB97M-V/def2-SVPD/SMD", 
                    ["wB97X-V/def2-TZVPPD/SMD", "wB97M-V/def2-QZVPPD/SMD"])
            with_solvent (str): For property-based queries, ensure that the properties are calculated
                in a particular solvent
            electronic_energy (Tuple[float, float]): Minimum and maximum electronic energy
            ionization_energy (Tuple[float, float]): Minimum and maximum ionization energy
            electron_affinity (Tuple[float, float]): Minimum and maximum electron affinity
            reduction_free_energy (Tuple[float, float]): Minimum and maximum reduction free energy
            oxidation_free_energy (Tuple[float, float]): Minimum and maximum oxidation free energy
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]), or single formula (e.g., C2 H4).
            deprecated (bool): Whether the material is tagged as deprecated.
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            has_props: (List[HasProps]): The calculated properties available for the material.
            material_ids (List[MPID]): List of Materials Project IDs to return data for.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            sort_fields (List[str]): Fields used to sort results. Prefixing with '-' will sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SearchDoc to return data for.
                Default is material_id if all_fields is False.

        Returns:
        """

        query_params = defaultdict(dict)  # type: dict

        for param, value in locals().items():
            if param in min_max_name_dict and value:
                if isinstance(value, (int, float)):
                    value = (value, value)
                query_params.update(
                    {
                        f"{min_max_name_dict[param]}_min": value[0],
                        f"{min_max_name_dict[param]}_max": value[1],
                    }
                )

        if material_ids:
            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if deprecated is not None:
            query_params.update({"deprecated": deprecated})

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

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
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
