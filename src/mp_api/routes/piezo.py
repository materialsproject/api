from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from emmet.core.polar import PiezoelectricDoc


class PiezoRester(BaseRester[PiezoelectricDoc]):

    suffix = "piezoelectric"
    document_model = PiezoelectricDoc  # type: ignore
    primary_key = "material_id"

    def search_piezoelectric_docs(
        self,
        piezoelectric_modulus: Optional[Tuple[float, float]] = None,
        sort_fields: Optional[List[str]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            piezoelectric_modulus (Tuple[float,float]): Minimum and maximum of the
                piezoelectric modulus in C/m² to consider.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in PiezoDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([PiezoDoc]) List of piezoelectric documents
        """

        query_params = defaultdict(dict)  # type: dict

        if piezoelectric_modulus:
            query_params.update(
                {
                    "piezo_modulus_min": piezoelectric_modulus[0],
                    "piezo_modulus_max": piezoelectric_modulus[1],
                }
            )

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

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
