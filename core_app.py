from maggma.stores import JSONStore

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
from mp_api.tasks.models import TaskDoc

# Uncomment to use JSON store for development
core_store = JSONStore("./test_files/materials_Li_Fe_V.json")
task_store = JSONStore("./test_files/tasks_Li_Fe_V.json")

# Uncomment to establish remote connection via dumped store object
# core_store_json = os.environ.get("CORE_STORE", "core_store.json")
# core_store = loadfn(core_store_json)

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
                    default_fields=["task_id", "formula_pretty", "last_updated"],
                ),
            ],
        ),
        "tasks": Resource(
            task_store,
            TaskDoc,
            query_operators=[
                FormulaQuery(),
                PaginationQuery(),
                SparseFieldsQuery(
                    MaterialsCoreDoc,
                    default_fields=["task_id", "formula_pretty", "last_updated"],
                ),
            ],
        ),
    }
)

app = api.app
