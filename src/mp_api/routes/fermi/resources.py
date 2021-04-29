from mp_api.core.resource import GetResource
from mp_api.routes.fermi.models import FermiDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery


def fermi_resource(fermi_store):
    resource = GetResource(
        fermi_store,
        FermiDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(FermiDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
    )

    return resource
