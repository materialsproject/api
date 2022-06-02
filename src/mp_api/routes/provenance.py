from mp_api.core.client import BaseRester
from emmet.core.provenance import ProvenanceDoc
from typing import Optional, List


class ProvenanceRester(BaseRester[ProvenanceDoc]):

    suffix = "provenance"
    document_model = ProvenanceDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        deprecated: Optional[bool] = False,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query provenance docs using a variety of search criteria.

        Arguments:
            deprecated (bool): Whether the material is tagged as deprecated.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in Provenance to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([ProvenanceDoc]) List of provenance documents
        """

        query_params = {"deprecated": deprecated}  # type: dict

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
