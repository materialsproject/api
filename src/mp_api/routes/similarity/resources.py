from maggma.api.resource import ReadOnlyResource
from mp_api.routes.similarity.models import SimilarityDoc
from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def similarity_resource(similarity_store):
    resource = ReadOnlyResource(
        similarity_store,
        SimilarityDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(SimilarityDoc, default_fields=["material_id"]),
        ],
        tags=["Similarity"],
        enable_default_search=False,
        disable_validation=True,
    )

    return resource
