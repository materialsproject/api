from maggma.api.query_operator.dynamic import NumericQuery
from maggma.api.resource import ReadOnlyResource
from mp_api.routes.eos.models import EOSDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery


def eos_resource(eos_store):
    resource = ReadOnlyResource(
        eos_store,
        EOSDoc,
        query_operators=[
            NumericQuery(model=EOSDoc),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(EOSDoc, default_fields=["task_id"]),
        ],
        tags=["EOS"],
        disable_validation=True,
    )

    return resource
