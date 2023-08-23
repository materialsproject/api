from __future__ import annotations

import warnings

from emmet.core.robocrys import RobocrystallogapherDoc

from mp_api.client.core import BaseRester, MPRestError


class RobocrysRester(BaseRester[RobocrystallogapherDoc]):
    suffix = "materials/robocrys"
    document_model = RobocrystallogapherDoc  # type: ignore
    primary_key = "material_id"

    def search_robocrys_text(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "search_robocrys_text is deprecated. " "Please use search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

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
