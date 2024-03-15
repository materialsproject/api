from __future__ import annotations

from emmet.core.robocrys import RobocrystallogapherDoc

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids


class RobocrysRester(BaseRester[RobocrystallogapherDoc]):
    suffix = "materials/robocrys"
    document_model = RobocrystallogapherDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        keywords: list[str],
        num_chunks: int | None = None,
        chunk_size: int | None = 100,
    ):
        """Search text generated from Robocrystallographer.

        Arguments:
            keywords (List[str]): List of search keywords
            num_chunks (Optional[int]): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (Optional[int]): Number of data entries per chunk.

        Returns:
            robocrys_docs (List[RobocrystallogapherDoc]): List of robocrystallographer documents
        """
        keyword_string = ",".join(keywords)

        robocrys_docs = self._query_resource(
            criteria={"keywords": keyword_string, "_limit": chunk_size},
            suburl="text_search",
            use_document_model=True,
            chunk_size=chunk_size,
            num_chunks=num_chunks,
        ).get("data", None)

        if robocrys_docs is None:
            raise MPRestError("Cannot find any matches.")

        return robocrys_docs

    def search_docs(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[RobocrystallogapherDoc] | list[dict]:
        """Query robocrystallographer docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in RobocrystallogapherDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([RobocrystallogapherDoc], [dict]) List of robocrystallographer documents or dictionaries.
        """
        query_params = {}  # type: dict

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
