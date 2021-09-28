from maggma.api.resource import ReadOnlyResource
from emmet.core.oxidation_states import OxidationStateDoc

from maggma.api.query_operator import (
    PaginationQuery,
    SortQuery,
    SparseFieldsQuery,
)

from mp_api.routes.materials.query_operators import FormulaQuery
from mp_api.routes.oxidation_states.query_operators import PossibleOxiStateQuery


def oxi_states_resource(oxi_states_store):
    resource = ReadOnlyResource(
        oxi_states_store,
        OxidationStateDoc,
        query_operators=[
            FormulaQuery(),
            PossibleOxiStateQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                OxidationStateDoc, default_fields=["material_id", "last_updated"]
            ),
        ],
        tags=["Oxidation States"],
        disable_validation=True,
    )

    return resource
