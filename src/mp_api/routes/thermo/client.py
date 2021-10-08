from collections import defaultdict
from typing import Optional, List, Tuple
from mp_api.core.client import BaseRester
from emmet.core.thermo import ThermoDoc
from pymatgen.core.periodic_table import Element


class ThermoRester(BaseRester[ThermoDoc]):

    suffix = "thermo"
    document_model = ThermoDoc  # type: ignore
    supports_versions = True
    primary_key = "material_id"

    def search_thermo_docs(
        self,
        material_ids: Optional[List[str]] = None,
        chemsys_formula: Optional[str] = None,
        nelements: Optional[Tuple[int, int]] = None,
        is_stable: Optional[bool] = None,
        total_energy: Optional[Tuple[float, float]] = None,
        formation_energy: Optional[Tuple[float, float]] = None,
        energy_above_hull: Optional[Tuple[float, float]] = None,
        equilibrium_reaction_energy: Optional[Tuple[float, float]] = None,
        uncorrected_energy: Optional[Tuple[float, float]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            material_ids (List[str]): List of Materials Project IDs to return data for.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            nelements (Tuple[int,int]): Minimum and maximum number of elements in the material to consider.
            is_stable (bool): Whether the material is stable.
            total_energy (Tuple[float,float]): Minimum and maximum corrected total energy in eV/atom to consider.
            formation_energy (Tuple[float,float]): Minimum and maximum formation energy in eV/atom to consider.
            energy_above_hull (Tuple[float,float]): Minimum and maximum energy above the hull in eV/atom to consider.
            equilibrium_reaction_energy (Tuple[float,float]): Minimum and maximum equilibrium reaction energy
                in eV/atom to consider.
            uncorrected_energy (Tuple[float,float]): Minimum and maximum uncorrected total
                energy in eV/atom to consider.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ThermoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ThermoDoc]) List of thermo documents
        """

        query_params = defaultdict(dict)  # type: dict

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if material_ids:
            query_params.update({"material_ids": ",".join(material_ids)})

        if nelements:
            query_params.update(
                {"nelements_min": nelements[0], "nelements_max": nelements[1]}
            )

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        if sort_field:
            query_params.update({"sort_field": sort_field})

        if ascending is not None:
            query_params.update({"ascending": ascending})

        name_dict = {
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "energy_above_hull": "energy_above_hull",
            "equilibrium_reaction_energy": "equilibrium_reaction_energy_per_atom",
            "uncorrected_energy": "uncorrected_energy_per_atom",
        }

        for param, value in locals().items():
            if "energy" in param and value:
                query_params.update(
                    {
                        "{}_min".format(name_dict[param]): value[0],
                        "{}_max".format(name_dict[param]): value[1],
                    }
                )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
