from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester, MPRestError

import warnings


class PiezoRester(BaseRester):

    suffix = "piezoelectric"

    def get_piezo_from_material_id(self, material_id: str):
        """
        Get piezoelectric data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing piezoelectric data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

    def search_piezoelectric_docs(
        self,
        piezoelectric_modulus: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            piezoelectric_modulus (Tuple[float,float]): Minimum and maximum of the
                piezoelectric modulus in C/m² to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs only.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if piezoelectric_modulus:
            query_params.update(
                {
                    "piezo_modulus_min": piezoelectric_modulus[0],
                    "piezo_modulus_max": piezoelectric_modulus[1],
                }
            )

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
