from mp_api.core.resource import Resource
from mp_api.similarity.models import SimilarityDoc


def similarity_resource(similarity_store):
    resource = Resource(
        similarity_store,
        SimilarityDoc,
        tags=["Similarity"],
        enable_default_search=False,
    )

    return resource
