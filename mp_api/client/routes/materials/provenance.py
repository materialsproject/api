from __future__ import annotations

from emmet.core.provenance import ProvenanceDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ProvenanceRester(BaseRester[ProvenanceDoc]):
    suffix = "materials/provenance"
    document_model = ProvenanceDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        deprecated: bool | None = False,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query provenance docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
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

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
