from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from mp_api.core.client import BaseRester
from mp_api.substrates.models import SubstratesDoc


class SubstratesRester(BaseRester):

    suffix = "substrates"
    document_model = SubstratesDoc

    def search_substrates_docs(
        self,
        film_id: Optional[str] = None,
        substrate_id: Optional[str] = None,
        substrate_formula: Optional[str] = None,
        film_orientation: Optional[List[int]] = None,
        substrate_orientation: Optional[List[int]] = None,
        area: Optional[Tuple[float, float]] = None,
        energy: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            film_id (str): Materials Project ID of the film material.
            substrate_id (str): Materials Project ID of the substrate material.
            substrate_formula (str): Reduced formula of the substrate material.
            film_orientation (List[int]): Vector indicating the surface orientation of the film material.
            substrate_orientation (List[int]): Vector indicating the surface orientation of the substrate material.
            area (Tuple[float,float]): Minimum and maximum volume in Å² to consider for the minimim coincident
                interface area range.
            energy (Tuple[float,float]): Minimum and maximum energy in meV to consider for the elastic energy range.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in SubstratesDoc to return data for.
                Default is the film_id and substrate_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs for the film and substrate only.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if film_id:
            query_params.update({"film_id": film_id})

        if substrate_id:
            query_params.update({"substrate_id": substrate_id})

        if substrate_formula:
            query_params.update({"substrate_formula": substrate_formula})

        if film_orientation:
            query_params.update(
                {"film_orientation": ",".join([str(i) for i in film_orientation])}
            )

        if substrate_orientation:
            query_params.update(
                {
                    "substrate_orientation": ",".join(
                        [str(i) for i in substrate_orientation]
                    )
                }
            )

        if area:
            query_params.update({"area_min": area[0], "area_max": area[1]})

        if energy:
            query_params.update({"energy_min": energy[0], "energy_max": energy[1]})

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
