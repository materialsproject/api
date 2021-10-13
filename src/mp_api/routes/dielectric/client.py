from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.routes.dielectric.models import DielectricDoc


class DielectricRester(BaseRester[DielectricDoc]):

    suffix = "dielectric"
    document_model = DielectricDoc  # type: ignore
    primary_key = "task_id"

    def search_dielectric_docs(
        self,
        e_total: Optional[Tuple[float, float]] = None,
        e_ionic: Optional[Tuple[float, float]] = None,
        e_electronic: Optional[Tuple[float, float]] = None,
        n: Optional[Tuple[float, float]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query dielectric docs using a variety of search criteria.

        Arguments:
            e_total (Tuple[float,float]): Minimum and maximum total dielectric constant to consider.
            e_ionic (Tuple[float,float]): Minimum and maximum ionic dielectric constant to consider.
            e_electronic (Tuple[float,float]): Minimum and maximum electronic dielectric constant to consider.
            n (Tuple[float,float]): Minimum and maximum refractive index to consider.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in DielectricDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([DielectricDoc]) List of dielectric documents.
        """

        query_params = defaultdict(dict)  # type: dict

        if e_total:
            query_params.update({"e_total_min": e_total[0], "e_total_max": e_total[1]})

        if e_ionic:
            query_params.update({"e_ionic_min": e_ionic[0], "e_ionic_max": e_ionic[1]})

        if e_electronic:
            query_params.update(
                {
                    "e_electronic_min": e_electronic[0],
                    "e_electronic_max": e_electronic[1],
                }
            )

        if n:
            query_params.update({"n_min": n[0], "n_max": n[1]})

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
