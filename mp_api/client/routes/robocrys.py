from typing import List, Optional

from mp_api.client.core import BaseRester, MPRestError
from emmet.core.robocrys import RobocrystallogapherDoc

import warnings


class RobocrysRester(BaseRester[RobocrystallogapherDoc]):

    suffix = "robocrys"
    document_model = RobocrystallogapherDoc  # type: ignore
    primary_key = "material_id"

    def search_robocrys_text(self, *args, **kwargs):  # pragma: no cover
        """
        Deprecated
        """

        warnings.warn(
            "search_robocrys_text is deprecated. " "Please use search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        keywords: List[str],
        num_chunks: Optional[int] = None,
        chunk_size: Optional[int] = 100,
    ):
        """
        Search text generated from Robocrystallographer.

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
            chunk_size=100,
        ).get("data", None)

        if robocrys_docs is None:
            raise MPRestError("Cannot find any matches.")

        return robocrys_docs
