from maggma.api.resource import ReadOnlyResource
from mp_api.routes.charge_density.models import ChgcarDataDoc
from maggma.api.query_operator import SparseFieldsQuery


def charge_density_resource(s3_store):
    resource = ReadOnlyResource(
        s3_store,
        ChgcarDataDoc,
        tags=["Charge Density"],
        enable_default_search=False,
        enable_get_by_key=True,
    )

    return resource
