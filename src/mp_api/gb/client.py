from typing import List, Optional, Tuple
from collections import defaultdict
import warnings

from mp_api.core.client import BaseRester

from mp_api.gb.models import GBTypeEnum, GBDoc


class GBRester(BaseRester):

    suffix = "gb"
    document_model = GBDoc  # type: ignore

    def search_gb_docs(
        self,
        task_ids: Optional[List[str]] = None,
        gb_energy: Optional[Tuple[float, float]] = None,
        separation_energy: Optional[Tuple[float, float]] = None,
        rotation_angle: Optional[Tuple[float, float]] = None,
        sigma: Optional[int] = None,
        type: Optional[GBTypeEnum] = None,
        chemsys: Optional[str] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query grain boundary docs using a variety of search criteria.

        Arguments:
            task_ids (List[str]): List of Materials Project IDs to query with.
            gb_energy (Tuple[float,float]): Minimum and maximum grain boundary energy in J/m³ to consider.
            separation_energy (Tuple[float,float]): Minimum and maximum work of separation energy in J/m³ to consider.
            rotation_angle (Tuple[float,float]): Minimum and maximum rotation angle in degrees to consider.
            sigma (int): Sigma value of grain boundary.
            type (GBTypeEnum): Grain boundary type.
            chemsys (str): Dash-delimited string of elements in the material.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in GBDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs and last updated data.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

        if task_ids:
            query_params.update({"task_ids": ",".join(task_ids)})

        if gb_energy:
            query_params.update(
                {"gb_energy_min": gb_energy[0], "gb_energy_max": gb_energy[1]}
            )

        if separation_energy:
            query_params.update(
                {
                    "w_sep_energy_min": separation_energy[0],
                    "w_sep_energy_max": separation_energy[1],
                }
            )

        if rotation_angle:
            query_params.update(
                {
                    "rotation_angle_min": rotation_angle[0],
                    "rotation_angle_max": rotation_angle[1],
                }
            )

        if sigma:
            query_params.update({"sigma": sigma})

        if type:
            query_params.update({"type": type})

        if chemsys:
            query_params.update({"chemsys": chemsys})

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
