from mp_api.client.core import BaseRester
from emmet.core.similarity import SimilarityDoc


class SimilarityRester(BaseRester[SimilarityDoc]):

    suffix = "similarity"
    document_model = SimilarityDoc  # type: ignore
    primary_key = "material_id"

    def search(*args, **kwargs):  # pragma: no cover
        raise NotImplementedError(
            """
            The SimilarityRester.search method does not exist as no search endpoint is present.
            Use get_data_by_id instead.
            """
        )
