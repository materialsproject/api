from mp_api.core.resource import GetResource
from mp_api.eos.models import EOSDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.eos.query_operators import EnergyVolumeQuery


def eos_resource(eos_store):
    resource = GetResource(
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
