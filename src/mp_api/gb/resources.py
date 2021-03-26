from mp_api.core.resource import GetResource
from mp_api.gb.models import GBDoc

from mp_api.gb.query_operators import GBEnergyQuery, GBStructureQuery, GBTaskIDQuery
from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery


def gb_resource(gb_store):
    resource = GetResource(
        gb_store,
        GBDoc,
        query_operators=[
            GBTaskIDQuery(),
            GBEnergyQuery(),
            GBStructureQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(GBDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Grain Boundaries"],
        enable_get_by_key=False,
    )

    return resource
