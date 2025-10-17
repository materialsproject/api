from __future__ import annotations

from collections import defaultdict

from emmet.core.alloys import AlloyPairDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class AlloysRester(BaseRester):
    suffix = "materials/alloys"
    document_model = AlloyPairDoc  # type: ignore
    primary_key = "pair_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        formulae: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[AlloyPairDoc] | list[dict]:
        """Query for hypothetical alloys formed between two commensurate
        crystal structures, following the methodology in
        https://doi.org/10.48550/arXiv.2206.10715.

        Please cite the relevant publication if data provided by this
        endpoint is useful.

        Arguments:
            material_ids (str, List[str]): Search for alloys containing the specified Material IDs
            formulae (List[str]): Search for alloys containing the specified formulae
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in AlloyPairDoc to return data for.

        Returns:
            ([AlloyPairDoc], [dict]) List of alloy pair documents or dictionaries.
        """
        query_params = defaultdict(dict)  # type: dict

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        return super()._search(
            formulae=formulae,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
