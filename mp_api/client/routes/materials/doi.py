from __future__ import annotations

from collections import defaultdict

from emmet.core.dois import DOIDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class DOIRester(BaseRester):
    suffix = "doi"
    document_model = DOIDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[DOIDoc] | list[dict]:
        """Query for DOI data.

        Arguments:
            material_ids (str, List[str]): Search for DOI data associated with the specified Material IDs
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in DOIDoc to return data for.

        Returns:
            ([DOIDoc], [dict]) List of DOIDoc documents or dictionaries.
        """
        query_params: dict = defaultdict(dict)

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
