from maggma.api.resource import ReadOnlyResource
from mp_api.routes.magnetism.models import MagnetismDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.magnetism.query_operators import MagneticQuery


def magnetism_resource(magnetism_store):
    resource = ReadOnlyResource(
        magnetism_store,
        MagnetismDoc,
        query_operators=[
            MagneticQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(MagnetismDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Magnetism"],
        disable_validation=True,
    )

    return resource
