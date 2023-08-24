from __future__ import annotations

from emmet.core.similarity import SimilarityDoc

from mp_api.client.core import BaseRester


class SimilarityRester(BaseRester[SimilarityDoc]):
    suffix = "materials/similarity"
    document_model = SimilarityDoc  # type: ignore
    primary_key = "material_id"

    def search(*args, **kwargs):  # pragma: no cover
        raise NotImplementedError(
            """
            The SimilarityRester.search method does not exist as no search endpoint is present.
            Use get_data_by_id instead.
            """
        )
