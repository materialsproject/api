from mp_api.core.resource import GetResource
from mp_api.routes.magnetism.models import MagnetismDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.magnetism.query_operators import MagneticQuery


def magnetism_resource(magnetism_store):
    resource = GetResource(
        magnetism_store,
        MagnetismDoc,
        query_operators=[
            MagneticQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(MagnetismDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Magnetism"],
    )

    return resource
