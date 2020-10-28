from mp_api.core.resource import Resource
from mp_api.piezo.models import PiezoDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.piezo.query_operators import PiezoelectricQuery


def piezo_resource(piezo_store):
    resource = Resource(
        piezo_store,
        PiezoDoc,
        query_operators=[
            PiezoelectricQuery(),
            PaginationQuery(),
            SparseFieldsQuery(PiezoDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Piezoelectric"],
    )

    return resource
