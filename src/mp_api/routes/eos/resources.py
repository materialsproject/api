from maggma.api.resource import ReadOnlyResource
from mp_api.routes.eos.models import EOSDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.eos.query_operators import EnergyVolumeQuery


def eos_resource(eos_store):
    resource = ReadOnlyResource(
        eos_store,
        EOSDoc,
        query_operators=[
            EnergyVolumeQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(EOSDoc, default_fields=["task_id"]),
        ],
        tags=["EOS"],
    )

    return resource
