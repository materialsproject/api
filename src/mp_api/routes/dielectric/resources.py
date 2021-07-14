from maggma.api.resource import ReadOnlyResource
from mp_api.routes.dielectric.models import DielectricDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.dielectric.query_operators import DielectricQuery


def dielectric_resource(dielectric_store):
    resource = ReadOnlyResource(
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
        disable_validation=True,
    )

    return resource
