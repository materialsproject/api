from collections import defaultdict
from typing import Optional, List, Tuple
from mp_api.core.client import BaseRester
from emmet.core.thermo import ThermoDoc
from pymatgen.core.periodic_table import Element


class ThermoRester(BaseRester):

    suffix = "thermo"
    document_model = ThermoDoc  # type: ignore
    supports_versions = True

    def search_thermo_docs(
        self,
        version: Optional[str] = None,
        material_ids: Optional[List[str]] = None,
        chemsys: Optional[str] = None,
        elements: Optional[List[Element]] = None,
        nelements: Optional[Tuple[int, int]] = None,
        is_stable: Optional[bool] = None,
        total_energy: Optional[Tuple[int, int]] = None,
        formation_energy: Optional[Tuple[int, int]] = None,
        energy_above_hull: Optional[Tuple[int, int]] = None,
        equillibrium_reaction_energy: Optional[Tuple[int, int]] = None,
        uncorrected_energy: Optional[Tuple[int, int]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            version (str): Version of data to query on in the format 'YYYY.MM.DD'. Defaults to None which will
                return data from the most recent database release.
            material_ids (List[str]): List of Materials Project IDs to return data for.
            chemsys (str): A chemical system (e.g., Li-Fe-O).
            elements (List[str]): List of elements in the material composition.
            nelements (Tuple[int,int]): Minimum and maximum number of elements in the material to consider.
            is_stable (bool): Whether the material is stable.
            total_energy (Tuple[int,int]): Minimum and maximum corrected total energy in eV/atom to consider.
            formation_energy (Tuple[int,int]): Minimum and maximum formation energy in eV/atom to consider.
            energy_above_hull (Tuple[int,int]): Minimum and maximum energy above the hull in eV/atom to consider.
            equillibrium_reaction_energy (Tuple[int,int]): Minimum and maximum equilibrium reaction energy
                in eV/atom to consider.
            uncorrected_energy (Tuple[int,int]): Minimum and maximum uncorrected total energy in eV/atom to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ThermoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ThermoDoc]) List of thermo documents
        """

        query_params = defaultdict(dict)  # type: dict

        if version:
            query_params.update({"version": version})

        if chemsys:
            query_params.update({"chemsys": chemsys})

        if material_ids:
            query_params.update({"task_ids": ",".join(material_ids)})

        if elements:
            query_params.update(
                {"elements": ",".join([str(element) for element in elements])}
            )

        if nelements:
            query_params.update(
                {"nelements_min": nelements[0], "nelements_max": nelements[1]}
            )

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        name_dict = {
            "total_energy": "energy_per_atom",
            "formation_energy": "formation_energy_per_atom",
            "energy_above_hull": "energy_above_hull",
            "equillibrium_reaction_energy": "equillibrium_reaction_energy_per_atom",
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
            version=self.version,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
