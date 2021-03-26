from mp_api.core.resource import GetResource
from mp_api.elasticity.models import ElasticityDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.elasticity.query_operators import (
    ChemsysQuery,
    BulkModulusQuery,
    ShearModulusQuery,
    PoissonQuery,
)


def elasticity_resource(elasticity_store):
    resource = GetResource(
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
    )

    return resource
