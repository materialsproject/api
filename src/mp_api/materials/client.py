from typing import List, Optional, Tuple

from mp_api.materials.models import Structure
from mp_api.materials.models.doc import CrystalSystem

from mp_api.core.client import BaseRester, MPRestError


class MaterialsRester(BaseRester):

    suffix = "materials"

    def get_structure_by_material_id(
        self, material_id: str, version: Optional[str] = None
    ) -> Structure:
        """
        Get a structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            version (str): Version of data to query on in the format 'YYYY.MM.DD'.
                Defaults to None which will return data from the most recent database release.


        Returns:
            structure (Structure): Pymatgen structure object
        """
        if version is None:
            result = self._make_request("{}/?fields=structure".format(material_id))
        else:
            result = self._make_request(
                "{}/?version={}&fields=structure".format(material_id, version)
            )

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError(f"No document found for {material_id}")

    def search_material_docs(
        self,
        version: Optional[str] = None,
        chemsys_formula: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
        crystal_system: Optional[CrystalSystem] = None,
        spacegroup_number: Optional[int] = None,
        spacegroup_symbol: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        deprecated: Optional[bool] = False,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query core material docs using a variety of search criteria.

        Arguments:
            version (str): Version of data to query on in the format 'YYYY.MM.DD'. Defaults to None which will
                return data from the most recent database release.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            task_ids (List[str]): List of Materials Project IDs to return data for.
            crystal_system (CrystalSystem): Crystal system of material.
            spacegroup_number (int): Space group number of material.
            spacegroup_symbol (str): Space group symbol of the material in international short symbol notation.
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in MaterialsCoreDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {"deprecated": deprecated}  # type: dict

        if version:
            query_params.update({"version": version})

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

        if task_ids:
            query_params.update({"task_ids": ",".join(task_ids)})

        query_params.update(
            {"crystal_system": crystal_system, "spacegroup_number": spacegroup_number}
        )

        if nsites:
            query_params.update({"nsites_min": nsites[0], "nsites_max": nsites[1]})

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if density:
            query_params.update({"density_min": density[0], "density_max": density[1]})

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results

    def get_database_versions(self):
        """
        Get version tags available for the Materials Project core materials data.
        These can be used to request data from previous releases.

        Returns:
            versions (List[str]): List of database versions as strings.
        """

        result = self._make_request("versions")

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No data found")
