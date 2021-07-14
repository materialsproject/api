from maggma.api.resource import ReadOnlyResource
from mp_api.routes.substrates.models import SubstratesDoc

from maggma.api.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
    NumericQuery,
    StringQueryOperator,
)
from mp_api.routes.substrates.query_operators import SubstrateStructureQuery


def substrates_resource(substrates_store):
    resource = ReadOnlyResource(
        substrates_store,
        SubstratesDoc,
        query_operators=[
            SubstrateStructureQuery(),
            NumericQuery(model=SubstratesDoc),
            StringQueryOperator(
                model=SubstratesDoc, excluded_fields=["film_orient", "orient"]
            ),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SubstratesDoc, default_fields=["film_id", "sub_id"]),
        ],
        tags=["Substrates"],
        enable_get_by_key=False,
        disable_validation=True,
    )

    return resource
