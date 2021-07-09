from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from mp_api.routes.surface_properties.models import SurfacePropDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.surface_properties.query_operators import ReconstructedQuery


def surface_props_resource(surface_prop_store):
    resource = ReadOnlyResource(
        surface_prop_store,
        SurfacePropDoc,
        query_operators=[
            NumericQuery(model=SurfacePropDoc),
            ReconstructedQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SurfacePropDoc, default_fields=["task_id"]),
        ],
        tags=["Surface Properties"],
        disable_validation=True,
    )

    return resource
