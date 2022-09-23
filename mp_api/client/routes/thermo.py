import warnings
from collections import defaultdict
from typing import List, Optional, Tuple, Union

from emmet.core.thermo import ThermoDoc
from pymatgen.analysis.phase_diagram import PhaseDiagram

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ThermoRester(BaseRester[ThermoDoc]):

    suffix = "thermo"
    document_model = ThermoDoc  # type: ignore
    supports_versions = True
    primary_key = "material_id"

    def search_thermo_docs(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "MPRester.thermo.search_thermo_docs is deprecated. "
            "Please use MPRester.thermo.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        chemsys: Optional[Union[str, List[str]]] = None,
        energy_above_hull: Optional[Tuple[float, float]] = None,
        equilibrium_reaction_energy: Optional[Tuple[float, float]] = None,
        formation_energy: Optional[Tuple[float, float]] = None,
        formula: Optional[Union[str, List[str]]] = None,
        is_stable: Optional[bool] = None,
        material_ids: Optional[List[str]] = None,
        num_elements: Optional[Tuple[int, int]] = None,
        total_energy: Optional[Tuple[float, float]] = None,
        uncorrected_energy: Optional[Tuple[float, float]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            energy_above_hull (Tuple[float,float]): Minimum and maximum energy above the hull in eV/atom to consider.
            equilibrium_reaction_energy (Tuple[float,float]): Minimum and maximum equilibrium reaction energy
                in eV/atom to consider.
            formation_energy (Tuple[float,float]): Minimum and maximum formation energy in eV/atom to consider.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            is_stable (bool): Whether the material is stable.
            material_ids (List[str]): List of Materials Project IDs to return data for.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements in the material to consider.
            total_energy (Tuple[float,float]): Minimum and maximum corrected total energy in eV/atom to consider.
            uncorrected_energy (Tuple[float,float]): Minimum and maximum uncorrected total
                energy in eV/atom to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ThermoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ThermoDoc]) List of thermo documents
        """

        query_params = defaultdict(dict)  # type: dict

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if material_ids:
            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if is_stable is not None:
            query_params.update({"is_stable": is_stable})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

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
                        f"{name_dict[param]}_min": value[0],
                        f"{name_dict[param]}_max": value[1],
                    }
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

    def get_phase_diagram_from_chemsys(self, chemsys: str) -> PhaseDiagram:
        """
        Get a pre-computed phase diagram for a given chemsys.

        Arguments:
            material_id (str): Materials project ID
        Returns:
            phase_diagram (PhaseDiagram): Pymatgen phase diagram object.
        """

        response = self._query_resource(
            fields=["phase_diagram"],
            suburl=f"phase_diagram/{chemsys}",
            use_document_model=False,
            num_chunks=1,
            chunk_size=1,
        ).get("data")

        return response[0]["phase_diagram"]  # type: ignore
