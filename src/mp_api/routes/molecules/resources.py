from maggma.api.resource import ReadOnlyResource
from mp_api.routes.molecules.models import MoleculesDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.molecules.query_operators import (
    MoleculeBaseQuery,
    MoleculeElementsQuery,
    MoleculeFormulaQuery,
)
from mp_api.routes.tasks.query_operators import MultipleTaskIDsQuery


def molecules_resource(molecules_store):
    resource = ReadOnlyResource(
        molecules_store,
        MoleculesDoc,
        query_operators=[
            MoleculeBaseQuery(),
            MoleculeElementsQuery(),
            MoleculeFormulaQuery(),
            MultipleTaskIDsQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(MoleculesDoc, default_fields=["task_id"]),
        ],
        tags=["Molecules"],
        disable_validation=True,
    )

    return resource
