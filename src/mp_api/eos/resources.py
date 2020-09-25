from mp_api.core.resource import Resource
from mp_api.eos.models import EOSDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.eos.query_operators import EnergyVolumeQuery


def eos_resource(eos_store):
    resource = Resource(
        eos_store,
        EOSDoc,
        query_operators=[
            EnergyVolumeQuery(),
            PaginationQuery(),
            SparseFieldsQuery(EOSDoc, default_fields=["task_id"]),
        ],
        tags=["EOS"],
    )

    return resource
