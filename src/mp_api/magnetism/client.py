from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from mp_api.core.client import BaseRester, MPRestError
from mp_api.magnetism.models import MagnetismDoc, MagneticOrderingEnum, TotalMagNormalizationEnum


class MagnetismRester(BaseRester):

    suffix = "magnetism"
    document_model = MagnetismDoc

    def search_magnetism_docs(
        self,
        ordering: Optional[MagneticOrderingEnum] = None,
        total_magnetization: Optional[Tuple[float, float]] = None,
        total_magnetization_normalization: Optional[TotalMagNormalizationEnum] = None,
        num_magnetic_sites: Optional[Tuple[float, float]] = None,
        num_unique_magnetic_sites: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query magnetism docs using a variety of search criteria.

        Arguments:
            ordering (MagneticOrderingEnum]): The magnetic ordering of the material.
            total_magnetization (Tuple[float,float]): Minimum and maximum total magnetization values to consider.
            total_magnetization_normalization (TotalMagNormalizationEnum): Type of normalization applied to values
                of total_magnetization supplied.
            num_magnetic_sites (Tuple[float,float]): Minimum and maximum number of magnetic sites to consider.
            num_unique_magnetic_sites (Tuple[float,float]): Minimum and maximum number of unique magnetic sites
                to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in MagnetismDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs only.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if total_magnetization:
            query_params.update(
                {
                    "total_magnetization_min": total_magnetization[0],
                    "total_magnetization_max": total_magnetization[1],
                }
            )

        if total_magnetization_normalization:
            query_params.update(
                {
                    "total_magnetization_normalization": total_magnetization_normalization.value,
                }
            )

        if num_magnetic_sites:
            query_params.update(
                {
                    "num_magnetic_sites_min": num_magnetic_sites[0],
                    "num_magnetic_sites_max": num_magnetic_sites[1],
                }
            )

        if num_unique_magnetic_sites:
            query_params.update(
                {
                    "num_unique_magnetic_sites_min": num_unique_magnetic_sites[0],
                    "num_unique_magnetic_sites_max": num_unique_magnetic_sites[1],
                }
            )

        if ordering:
            query_params.update({"ordering": ordering.value})

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
            for result in results:
                yield result
