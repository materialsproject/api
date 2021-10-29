from maggma.api.resource import ReadOnlyResource
from emmet.core.bonds import BondingDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery

from mp_api.routes.bonds.query_operators import BondLengthQuery, CoordinationEnvsQuery


def bonds_resource(bonds_store):
    resource = ReadOnlyResource(
        bonds_store,
        BondingDoc,
        query_operators=[
            BondLengthQuery(),
            CoordinationEnvsQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                BondingDoc, default_fields=["material_id", "last_updated"],
            ),
        ],
        tags=["Bonds"],
        disable_validation=True,
    )

    return resource
