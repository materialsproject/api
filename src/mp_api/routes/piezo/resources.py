from maggma.api.resource import ReadOnlyResource
from emmet.core.polar import PiezoelectricDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.piezo.query_operators import PiezoelectricQuery


def piezo_resource(piezo_store):
    resource = ReadOnlyResource(
        piezo_store,
        PiezoelectricDoc,
        query_operators=[
            PiezoelectricQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                PiezoelectricDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Piezoelectric"],
        disable_validation=True,
    )

    return resource
