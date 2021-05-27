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
        volume: Optional[Tuple[float, float]] = None,
        energy: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

        Arguments:
            volume (Tuple[float,float]): Minimum and maximum volume in A³/atom to consider for EOS plot range.
            energy (Tuple[float,float]): Minimum and maximum energy in eV/atom to consider for EOS plot range.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only if all_fields is False.

        Returns:
            ([EOSDoc]) List of eos documents
        """

        query_params = defaultdict(dict)  # type: dict

        if volume:
            query_params.update({"volume_min": volume[0], "volume_max": volume[1]})

        if energy:
            query_params.update({"energy_min": energy[0], "energy_max": energy[1]})

        query_params = {entry: query_params[entry] for entry in query_params if query_params[entry] is not None}

        return super().search(
            version=self.version,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
