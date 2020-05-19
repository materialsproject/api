import os
from monty.serialization import loadfn

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import (
    FormulaQuery,
    DeprecationQuery,
    MinMaxQuery,
    SymmetryQuery,
)
from mp_api.materials.models.doc import MaterialsCoreDoc

from mp_api.core.resource import Resource
from mp_api.core.api import MAPI


core_store_json = os.environ.get("CORE_STORE", "core_store.json")
core_store = loadfn(core_store_json)

api = MAPI(
    resources={
        "core": Resource(
            core_store,
            MaterialsCoreDoc,
            query_operators=[
                FormulaQuery(),
                SymmetryQuery(),
                DeprecationQuery(),
                MinMaxQuery(),
                PaginationQuery(),
                SparseFieldsQuery(
                    MaterialsCoreDoc,
                    default_fields=["task_id", "formula_pretty", "last_updated",],
                ),
            ],
        )
    }
)

app = api.app
