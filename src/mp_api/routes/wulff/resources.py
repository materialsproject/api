from maggma.api.resource import ReadOnlyResource
from mp_api.routes.wulff.models import WulffDoc

from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def wulff_resource(wulff_store):
    resource = ReadOnlyResource(
        wulff_store,
        WulffDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(WulffDoc, default_fields=["task_id"]),
        ],
        tags=["Surface Properties"],
        enable_default_search=False,
        disable_validation=True,
    )

    return resource
