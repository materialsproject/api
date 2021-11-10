from maggma.api.resource import ReadOnlyResource
from emmet.core.polar import DielectricDoc

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
                DielectricDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Dielectric"],
        disable_validation=True,
    )

    return resource
