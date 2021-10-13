from maggma.api.resource import ReadOnlyResource
from maggma.api.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.routes.charge_density.models import ChgcarDataDoc
from mp_api.routes.charge_density.query_operators import ChgcarTaskIDQuery


def charge_density_resource(s3_store):
    resource = ReadOnlyResource(
        s3_store,
        ChgcarDataDoc,
        query_operators=[
            ChgcarTaskIDQuery(),
            PaginationQuery(default_limit=5, max_limit=10),
            SparseFieldsQuery(
                ChgcarDataDoc, default_fields=["task_id", "last_updated"],
            ),
        ],
        tags=["Charge Density"],
        enable_default_search=True,
        enable_get_by_key=True,
        disable_validation=True,
    )

    return resource
