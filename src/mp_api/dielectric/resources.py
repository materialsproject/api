from mp_api.core.resource import Resource
from mp_api.dielectric.models import DielectricDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.dielectric.query_operators import DielectricQuery


def dielectric_resource(dielectric_store):
    resource = Resource(
        dielectric_store,
        DielectricDoc,
        query_operators=[
            DielectricQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                DielectricDoc, default_fields=["task_id", "last_updated"]
            ),
        ],
        tags=["Dielectric"],
    )

    return resource
