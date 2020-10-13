from mp_api.core.resource import Resource
from mp_api.dois.models import DOIDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def dois_resource(dois_store):
    resource = Resource(
        dois_store,
        DOIDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(DOIDoc, default_fields=["task_id", "doi"]),
        ],
        tags=["DOIs"],
        enable_default_search=False,
    )

    return resource
