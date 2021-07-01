from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.routes.eos.models import EOSDoc


class EOSRester(BaseRester):

    suffix = "eos"
    document_model = EOSDoc  # type: ignore
    primary_key = "task_id"

    def search_eos_docs(
        self,
        volumes: Optional[Tuple[float, float]] = None,
        energies: Optional[Tuple[float, float]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            volumes (Tuple[float,float]): Minimum and maximum volume in A³/atom to consider for EOS plot range.
            energies (Tuple[float,float]): Minimum and maximum energy in eV/atom to consider for EOS plot range.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only if all_fields is False.

        Returns:
            ([EOSDoc]) List of eos documents
        """

        query_params = defaultdict(dict)  # type: dict

        if volumes:
            query_params.update({"volumes_min": volumes[0], "volumes_max": volumes[1]})

        if energies:
            query_params.update(
                {"energies_min": energies[0], "energies_max": energies[1]}
            )

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
