from mp_api.core.resource import Resource
from mp_api.gb.models import GBDoc

from mp_api.gb.query_operators import GBEnergyQuery, GBStructureQuery
from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def gb_resource(gb_store):
    resource = Resource(
        gb_store,
        GBDoc,
        query_operators=[
            GBEnergyQuery(),
            GBStructureQuery(),
            PaginationQuery(),
            SparseFieldsQuery(GBDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Grain Boundaries"],
    )

    return resource
