from __future__ import annotations

from emmet.core.fermi import FermiDoc

from mp_api.client.core import BaseRester


class FermiRester(BaseRester[FermiDoc]):
    suffix = "materials/fermi"
    document_model = FermiDoc  # type: ignore
    primary_key = "task_id"

    def search(
        self,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query fermi surface docs using a variety of search criteria.

        Arguments:
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in FermiDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([FermiDoc]) List of material documents
        """
        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )
