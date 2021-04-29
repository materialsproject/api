from mp_api.core.resource import GetResource
from mp_api.routes.dielectric.models import DielectricDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.dielectric.query_operators import DielectricQuery


def dielectric_resource(dielectric_store):
    resource = GetResource(
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
