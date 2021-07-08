from maggma.api.resource import ReadOnlyResource
from mp_api.routes.similarity.models import SimilarityDoc
from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def similarity_resource(similarity_store):
    resource = ReadOnlyResource(
        similarity_store,
        SimilarityDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(SimilarityDoc, default_fields=["task_id"]),
        ],
        tags=["Similarity"],
        enable_default_search=False,
        monty_encoded_response=True,
    )

    return resource
