from maggma.api.resource import ReadOnlyResource
from mp_api.routes.grain_boundary.models import GrainBoundaryDoc

from mp_api.routes.grain_boundary.query_operators import GBEnergyQuery, GBStructureQuery, GBTaskIDQuery
from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery


def gb_resource(gb_store):
    resource = ReadOnlyResource(
        gb_store,
        GrainBoundaryDoc,
        query_operators=[
            GBTaskIDQuery(),
            GBEnergyQuery(),
            GBStructureQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(GrainBoundaryDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Grain Boundaries"],
        enable_get_by_key=False,
    )

    return resource
