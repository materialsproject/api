from typing import List, Optional, Tuple
from mp_api.bandstructure.models.core import BSPathType, BSDataFields

from mp_api.core.client import BaseRester, MPRestError


class BSRester(BaseRester):

    suffix = "bs"

    def get_bandstructure_from_material_id(
        self, material_id: str, path_type: BSPathType
    ):
        """
        Get a band structure for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID
            path_type (BSPathType): Band structure type determined by the k-path convention used.


        Returns:
            bandstructure (BandStructureSymmLine): Pymatgen band structure object
        """

        result = self._make_request(
            "object/?task_id={}&path_type={}&all_fields=true".format(
                material_id, path_type.value
            )
        )

        if result.get("object", None) is not None:
            return result["object"]
        else:
            raise MPRestError("No document found")

    def get_bandstructure_summary_from_material_id(self, material_id: str):
        """
        Get a band structure summary doc for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            doc (dict): Band structure summary doc.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

    def search_bandstructure_docs(
        self,
        path_type: BSPathType,
        data_field: BSDataFields,
        energy: Tuple[float, float],
        direct: Optional[bool] = None,
        chemsys_formula: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = None,
        volume: Optional[Tuple[float, float]] = None,
        density: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query band structure summary docs using a variety of search criteria.

        Arguments:
            path_type (BSPathType): Band structure type determined by the k-path convention.
            data_field (BSDataFields): Data field to query on.
            energy (Tuple[int,int]): Minimum and maximum energy to consider.
            direct (bool): Whether the band gap is direct if it is chosen with data_field.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in BSDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {
            "path_type": path_type.value,
            "data_field": data_field.value,
            "energy_min": energy[0],
            "energy_max": energy[1],
        }

        if direct is not None:
            query_params.update({"direct": direct})

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

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
