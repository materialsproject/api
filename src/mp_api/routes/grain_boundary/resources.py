from maggma.api.resource import ReadOnlyResource
from mp_api.routes.grain_boundary.models import GrainBoundaryDoc

from mp_api.routes.grain_boundary.query_operators import (
    GBStructureQuery,
    GBTaskIDQuery,
)
from maggma.api.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    NumericQuery,
)


def gb_resource(gb_store):
    resource = ReadOnlyResource(
        gb_store,
        GrainBoundaryDoc,
        query_operators=[
            GBTaskIDQuery(),
            NumericQuery(
                model=GrainBoundaryDoc, excluded_fields=["rotation_axis", "gb_plane"]
            ),
            GBStructureQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                GrainBoundaryDoc, default_fields=["task_id", "last_updated"]
            ),
        ],
        tags=["Grain Boundaries"],
        enable_get_by_key=False,
        disable_validation=True,
    )

    return resource
