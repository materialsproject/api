from typing import List, Optional, Tuple
from pymatgen import Structure

from mp_api.core.client import RESTer, RESTError
from mp_api.materials.models.core import CrystalSystem


class CoreRESTer(RESTer):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the CoreRESTer to a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/core/", **kwargs)

    def get_structure_from_material_id(self, material_id: str):
        """
        Get a structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            structure (Structure): Pymatgen structure object
        """
        result = self._make_request("{}/?fields=structure".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise RESTError("No document found")

    def search_material_docs(
        self,
        chemsys_formula: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
        crystal_system: Optional[CrystalSystem] = None,
        spacegroup_number: Optional[int] = None,
        spacegroup_symbol: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = (None, None),
        volume: Optional[Tuple[float, float]] = (None, None),
        density: Optional[Tuple[float, float]] = (None, None),
        deprecated: Optional[bool] = False,
        limit: Optional[int] = 10,
        skip: Optional[int] = 0,
        fields: Optional[List[str]] = [None],
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            task_ids (List[str]): List of IDs to return data for.
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            limit (int): Maximum number of structures to return.
            skip (int): Number of entries to skip in the search.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Returns:
            ([dict]) List of dictionaries containing Materials Project IDs
                reduced chemical formulas, and last updated tags.
        """

        query_params = {"limit": limit, "skip": skip, "deprecated": deprecated}
        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if any(task_ids):
            query_params.update({"task_ids": ",".join(task_ids)})

        query_params.update(
            {
                "crystal_system": crystal_system,
                "spacegroup_number": spacegroup_number,
                "crystal_system": crystal_system,
            }
        )

        if any(nsites):
            query_params.update({"nsites_min": nsites[0], "nsites_max": nsites[1]})

        if any(volume):
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if any(density):
            query_params.update({"density_min": density[0], "density_max": density[1]})

        if any(fields):
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        results = self.query(query_params)

        return results.get("data", [])
