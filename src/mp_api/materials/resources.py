from mp_api.core.resource import Resource
from mp_api.materials.models.doc import MaterialsCoreDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import (
    FormulaQuery,
    DeprecationQuery,
    MinMaxQuery,
    SymmetryQuery,
    MultiTaskIDQuery,
)


def core_resource(core_store):
    resource = Resource(
        core_store,
        MaterialsCoreDoc,
        query_operators=[
            FormulaQuery(),
            MultiTaskIDQuery(),
            SymmetryQuery(),
            DeprecationQuery(),
            MinMaxQuery(),
            PaginationQuery(),
            SparseFieldsQuery(
                MaterialsCoreDoc,
                default_fields=["task_id", "formula_pretty", "last_updated"],
            ),
        ],
    )

    return resource

