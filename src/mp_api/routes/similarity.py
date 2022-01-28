from mp_api.core.client import BaseRester
from emmet.core.similarity import SimilarityDoc


class SimilarityRester(BaseRester[SimilarityDoc]):

    suffix = "similarity"
    document_model = SimilarityDoc  # type: ignore
    primary_key = "material_id"
