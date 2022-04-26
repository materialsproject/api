from typing import List, Optional, Tuple, Union
from pymatgen.core.structure import Structure

from emmet.core.vasp.material import MaterialsDoc
from emmet.core.symmetry import CrystalSystem
from emmet.core.settings import EmmetSettings

from mp_api.core.client import BaseRester, MPRestError
from mp_api.core.utils import validate_ids

_EMMET_SETTINGS = EmmetSettings()


class MaterialsRester(BaseRester[MaterialsDoc]):

    suffix = "materials"
    document_model = MaterialsDoc  # type: ignore
    supports_versions = True
    primary_key = "material_id"

    def get_structure_by_material_id(
        self, material_id: str, final: bool = True
    ) -> Union[Structure, List[Structure]]:
        """
        Get a structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            final (bool): Whether to get the final structure, or the list of initial
                (pre-relaxation) structures. Defaults to True.

        Returns:
            structure (Union[Structure, List[Structure]]): Pymatgen structure object or list of
                pymatgen structure objects.
        """
        if final:
            response = self.get_data_by_id(material_id, fields=["structure"])
            return response.structure if response is not None else response  # type: ignore
        else:
            response = self.get_data_by_id(material_id, fields=["initial_structures"])
            return response.initial_structures if response is not None else response  # type: ignore

    def search_material_docs(
        self,
        formula: Optional[str] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        crystal_system: Optional[CrystalSystem] = None,
        spacegroup_number: Optional[int] = None,
        spacegroup_symbol: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        deprecated: Optional[bool] = False,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            formula (str): A formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            task_ids (List[str]): List of Materials Project IDs to return data for.
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([MaterialsDoc]) List of material documents
        """

        query_params = {"deprecated": deprecated}  # type: dict

        if formula:
            query_params.update({"formula": formula})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if task_ids:
            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        query_params.update(
            {
                "crystal_system": crystal_system,
                "spacegroup_number": spacegroup_number,
                "spacegroup_symbol": spacegroup_symbol,
            }
        )

        if nsites:
            query_params.update({"nsites_min": nsites[0], "nsites_max": nsites[1]})

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if density:
            query_params.update({"density_min": density[0], "density_max": density[1]})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
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
            **query_params
        )

    def find_structure(
        self,
        filename_or_structure,
        ltol=_EMMET_SETTINGS.LTOL,
        stol=_EMMET_SETTINGS.STOL,
        angle_tol=_EMMET_SETTINGS.ANGLE_TOL,
        allow_multiple_results=False,
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

        params = {"ltol": ltol, "stol": stol, "angle_tol": angle_tol, "_limit": 1}

        if isinstance(filename_or_structure, str):
            s = Structure.from_file(filename_or_structure)
        elif isinstance(filename_or_structure, Structure):
            s = filename_or_structure
        else:
            raise MPRestError("Provide filename or Structure object.")

        results = self._post_resource(
            body=s.as_dict(),
            params=params,
            suburl="find_structure",
            use_document_model=False,
        ).get("data")

        if len(results) > 1:  # type: ignore
            if not allow_multiple_results:
                raise ValueError(
                    "Multiple matches found for this combination of tolerances, but "
                    "`allow_multiple_results` set to False."
                )
            return results  # type: ignore

        if results:
            return results[0]["material_id"]
        else:
            return []
