from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.routes.magnetism.models import MagnetismDoc

from pymatgen.analysis.magnetism import Ordering


class MagnetismRester(BaseRester[MagnetismDoc]):

    suffix = "magnetism"
    document_model = MagnetismDoc  # type: ignore
    primary_key = "task_id"

    def search_magnetism_docs(
        self,
        ordering: Optional[Ordering] = None,
        total_magnetization: Optional[Tuple[float, float]] = None,
        total_magnetization_normalized_vol: Optional[Tuple[float, float]] = None,
        total_magnetization_normalized_formula_units: Optional[
            Tuple[float, float]
        ] = None,
        num_magnetic_sites: Optional[Tuple[int, int]] = None,
        num_unique_magnetic_sites: Optional[Tuple[int, int]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query magnetism docs using a variety of search criteria.

        Arguments:
            ordering (Ordering]): The magnetic ordering of the material.
            total_magnetization (Tuple[float,float]): Minimum and maximum total magnetization values to consider.
            total_magnetization_normalized_vol (Tuple[float,float]): Minimum and maximum total magnetization values
                normalized by volume to consider.
            total_magnetization_normalized_formula_units (Tuple[float,float]): Minimum and maximum total magnetization
                values normalized by formula units to consider.
            num_magnetic_sites (Tuple[int,int]): Minimum and maximum number of magnetic sites to consider.
            num_unique_magnetic_sites (Tuple[int,int]): Minimum and maximum number of unique magnetic sites
                to consider.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MagnetismDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([MagnetismDoc]) List of magnetism documents
        """

        query_params = defaultdict(dict)  # type: dict

        if total_magnetization:
            query_params.update(
                {
                    "total_magnetization_min": total_magnetization[0],
                    "total_magnetization_max": total_magnetization[1],
                }
            )

        if total_magnetization_normalized_vol:
            query_params.update(
                {
                    "total_magnetization_normalized_vol_min": total_magnetization_normalized_vol[
                        0
                    ],
                    "total_magnetization_normalized_vol_max": total_magnetization_normalized_vol[
                        1
                    ],
                }
            )

        if total_magnetization_normalized_formula_units:
            query_params.update(
                {
                    "total_magnetization_normalized_formula_units_min": total_magnetization_normalized_formula_units[
                        0
                    ],
                    "total_magnetization_normalized_formula_units_max": total_magnetization_normalized_formula_units[
                        1
                    ],
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

        if sort_field:
            query_params.update({"sort_field": sort_field})

        if ascending is not None:
            query_params.update({"ascending": ascending})

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
