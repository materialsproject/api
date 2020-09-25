from typing import List, Optional, Tuple

from pymatgen.core.periodic_table import Element
from mp_api.dos.models.core import DOSProjection
from pymatgen.electronic_structure.core import Spin, OrbitalType

from mp_api.core.client import BaseRester, RESTError


class DOSRESTer(BaseRester):
    def __init__(self, endpoint, **kwargs):
        """
        Initializes the DOSRESTer with a MAPI URL
        """

        self.endpoint = endpoint.strip("/")

        super().__init__(endpoint=self.endpoint + "/dos/", **kwargs)

    def get_dos_from_material_id(self, material_id: str):
        """
        Get a density of states for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID


        Returns:
            dos (CompleteDos): Pymatgen density of states object
        """

        result = self._make_request(
            "object/?task_id={}&all_fields=true".format(material_id)
        )

        if result.get("object", None) is not None:
            return result["object"]
        else:
            raise RESTError("No document found")

    def get_dos_summary_from_material_id(self, material_id: str):
        """
        Get a density of states summary doc for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            doc (dict): Density of states summary doc.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise RESTError("No document found")

    def search_dos_docs(
        self,
        projection: DOSProjection = None,
        spin_channel: Spin = None,
        energy: Tuple[float, float] = (None, None),
        element: Optional[Element] = None,
        orbital: Optional[OrbitalType] = None,
        chemsys_formula: Optional[str] = None,
        nsites: Optional[Tuple[int, int]] = (None, None),
        volume: Optional[Tuple[float, float]] = (None, None),
        density: Optional[Tuple[float, float]] = (None, None),
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = 100,
        fields: Optional[List[str]] = [None],
    ):
        """
        Query density of states summary docs using a variety of search criteria.

        Arguments:
            projection (DOSProjection): Density of states projection type. 
            spin_channel (Spin): Spin channel to query on.
            energy (Tuple[int,int]): Minimum and maximum energy to consider.
            element (Element): Element in projection to consider.
            orbital (OrbitalType): Orbital in projection to consider.
            chemsys_formula (str): A chemical system (e.g., Li-Fe-O),
                or formula including anonomyzed formula
                or wild cards (e.g., Fe2O3, ABO3, Si*).
            nsites (Tuple[int,int]): Minimum and maximum number of sites to consider.
            volume (Tuple[float,float]): Minimum and maximum volume to consider.
            density (Tuple[float,float]): Minimum and maximum density to consider.
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in DOSDoc to return data for.
                Default is material_id, last_updated, and formula_pretty.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'. 
                Defaults to Materials Project IDs reduced chemical formulas, and last updated tags.
        """

        query_params = {
            "projection": projection.value,
            "spin_channel": str(spin_channel),
            "energy_min": energy[0],
            "energy_max": energy[1],
        }

        if element:
            query_params.update({"element": element.value})

        if orbital:
            query_params.update({"orbital": orbital.name})

        if chemsys_formula:
            query_params.update({"formula": chemsys_formula})

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

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results

