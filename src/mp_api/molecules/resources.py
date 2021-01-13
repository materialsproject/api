from mp_api.core.resource import Resource
from mp_api.molecules.models import MoleculesDoc

from mp_api.core.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.molecules.query_operators import (
    MoleculeBaseQuery,
    MoleculeElementsQuery,
    MoleculeFormulaQuery,
)
from mp_api.search.query_operators import SearchTaskIDsQuery


def molecules_resource(molecules_store):
    resource = Resource(
        molecules_store,
        MoleculesDoc,
        query_operators=[
            MoleculeBaseQuery(),
            MoleculeElementsQuery(),
            MoleculeFormulaQuery(),
            SearchTaskIDsQuery(),
            SortQuery(),
            PaginationQuery(),
            SparseFieldsQuery(MoleculesDoc, default_fields=["task_id"]),
        ],
        tags=["Molecules"],
    )

    return resource
