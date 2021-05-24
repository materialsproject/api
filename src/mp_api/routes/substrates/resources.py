from maggma.api.resource import ReadOnlyResource
from mp_api.routes.substrates.models import SubstratesDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.substrates.query_operators import SubstrateStructureQuery, EnergyAreaQuery


def substrates_resource(substrates_store):
    resource = ReadOnlyResource(
        substrates_store,
        SubstratesDoc,
        query_operators=[
            SubstrateStructureQuery(),
            EnergyAreaQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SubstratesDoc, default_fields=["film_id", "sub_id"]),
        ],
        tags=["Substrates"],
        enable_get_by_key=False,
    )

    return resource
