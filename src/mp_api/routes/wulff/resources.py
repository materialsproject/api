from mp_api.core.resource import GetResource
from mp_api.routes.wulff.models import WulffDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def wulff_resource(wulff_store):
    resource = GetResource(
        wulff_store,
        WulffDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(WulffDoc, default_fields=["task_id"]),
        ],
        tags=["Surface Properties"],
        enable_default_search=False,
    )

    return resource
