from mp_api.core.resource import Resource
from mp_api.surface_properties.models import SurfacePropDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.surface_properties.query_operators import (
    SurfaceMinMaxQuery,
    ReconstructedQuery,
)


def surface_props_resource(surface_prop_store):
    resource = Resource(
        surface_prop_store,
        SurfacePropDoc,
        query_operators=[
            SurfaceMinMaxQuery(),
            ReconstructedQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SurfacePropDoc, default_fields=["task_id"]),
        ],
        tags=["Surface Properties"],
    )

    return resource
