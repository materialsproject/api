from maggma.api.resource import ReadOnlyResource
from mp_api.routes.elasticity.models import ElasticityDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.elasticity.query_operators import (
    ChemsysQuery,
    BulkModulusQuery,
    ShearModulusQuery,
    PoissonQuery,
)


def elasticity_resource(elasticity_store):
    resource = ReadOnlyResource(
        elasticity_store,
        ElasticityDoc,
        query_operators=[
            ChemsysQuery(),
            BulkModulusQuery(),
            ShearModulusQuery(),
            PoissonQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                ElasticityDoc, default_fields=["task_id", "pretty_formula"],
            ),
        ],
        tags=["Elasticity"],
        disable_validation=False,
    )

    return resource
