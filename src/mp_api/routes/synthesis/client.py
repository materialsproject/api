from mp_api.core.client import BaseRester, MPRestError
from mp_api.routes.synthesis.models import SynthesisSearchResultModel
from typing import List


class SynthesisRester(BaseRester):

    suffix = "synthesis"
    document_model = SynthesisSearchResultModel  # type: ignore

    def search_synthesis_text(self, keywords: List[str]):
        """
        Search synthesis recipe text.
        Arguments:
            keywords (List[str]): List of search keywords
        Returns:
            synthesis_docs ([SynthesisDoc]): List of synthesis documents
        """

        keyword_string = ",".join(keywords)

        synthesis_docs = self._query_resource(
            criteria={"keywords": keyword_string}, use_document_model=True,
        ).get("data", None)

        if synthesis_docs is None:
            raise MPRestError("Cannot find any matches.")

        return synthesis_docs
