from mp_api.core.resource import Resource
from mp_api.substrates.models import SubstratesDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.substrates.query_operators import SubstrateStructureQuery, EnergyAreaQuery


def substrates_resource(substrates_store):
    resource = Resource(
        substrates_store,
        SubstratesDoc,
        query_operators=[
            SubstrateStructureQuery(),
            EnergyAreaQuery(),
            PaginationQuery(),
            SparseFieldsQuery(SubstratesDoc, default_fields=["film_id", "sub_id"]),
        ],
        tags=["Substrates"],
        enable_get_by_key=False,
    )

    return resource
