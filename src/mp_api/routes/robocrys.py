from typing import List

from mp_api.core.client import BaseRester, MPRestError
from emmet.core.robocrys import RobocrystallogapherDoc


class RobocrysRester(BaseRester[RobocrystallogapherDoc]):

    suffix = "robocrys"
    document_model = RobocrystallogapherDoc  # type: ignore
    primary_key = "material_id"

    def search_robocrys_text(self, keywords: List[str]):
        """
        Search text generated from Robocrystallographer.

        Arguments:
            keywords (List[str]): List of search keywords

        Returns:
            robocrys_docs (List[RobocrystallogapherDoc]): List of robocrystallographer documents
        """

        keyword_string = ",".join(keywords)

        robocrys_docs = self._query_resource(
            criteria={"keywords": keyword_string},
            suburl="text_search",
            use_document_model=True,
        ).get("data", None)

        if robocrys_docs is None:
            raise MPRestError("Cannot find any matches.")

        return robocrys_docs