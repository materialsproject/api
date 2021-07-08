from maggma.api.resource import ReadOnlyResource
from mp_api.routes.dois.models import DOIDoc

from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def dois_resource(dois_store):
    resource = ReadOnlyResource(
        dois_store,
        DOIDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(DOIDoc, default_fields=["task_id", "doi"]),
        ],
        tags=["DOIs"],
        enable_default_search=False,
        monty_encoded_response=True,
    )

    return resource
