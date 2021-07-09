from maggma.api.resource import ReadOnlyResource
from mp_api.routes.piezo.models import PiezoDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.piezo.query_operators import PiezoelectricQuery


def piezo_resource(piezo_store):
    resource = ReadOnlyResource(
        piezo_store,
        PiezoDoc,
        query_operators=[
            PiezoelectricQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(PiezoDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Piezoelectric"],
        disable_validation=True,
    )

    return resource
