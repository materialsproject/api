from mp_api.core.resource import Resource
from mp_api.magnetism.models import MagnetismDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.magnetism.query_operators import MagneticQuery


def magnetism_resource(magnetism_store):
    resource = Resource(
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
