from maggma.api.resource import ReadOnlyResource
from mp_api.routes.fermi.models import FermiDoc

from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery


def fermi_resource(fermi_store):
    resource = ReadOnlyResource(
        fermi_store,
        FermiDoc,
        query_operators=[
            PaginationQuery(),
            SparseFieldsQuery(FermiDoc, default_fields=["task_id", "last_updated"]),
        ],
        tags=["Electronic Structure"],
        disable_validation=True,
    )

    return resource
