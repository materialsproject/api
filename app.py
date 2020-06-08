import os
from monty.serialization import loadfn
from maggma.stores import JSONStore

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import (
    FormulaQuery,
    DeprecationQuery,
    MinMaxQuery,
    SymmetryQuery,
)
from mp_api.xas.query_operator import XASQuery

from mp_api.materials.models.doc import MaterialsCoreDoc
from mp_api.tasks.models import TaskDoc
from mp_api.xas.models import XASDoc

from mp_api.core.resource import Resource
from mp_api.core.api import MAPI


resources = {}

# Uncomment to use JSON store for development
# core_store = JSONStore("./test_files/materials_Li_Fe_V.json")
# task_store = JSONStore("./test_files/tasks_Li_Fe_V.json")

# Materials core store
core_store_json = os.environ.get("CORE_STORE", "core_store.json")
core_store = loadfn(core_store_json)
resources.update(
    {
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
        )
    }
)

# Tasks store
task_store_json = os.environ.get("TASK_STORE", "task_store.json")
task_store = loadfn(task_store_json)
resources.update(
    {
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
        )
    }
)

# XAS store
db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)
xas_store_json = os.environ.get("XAS_STORE", "xas_store.json")
if db_uri:
    from maggma.stores import MongoURIStore

    xas_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="xas_id",
        collection_name="xas",
    )
else:
    xas_store = loadfn(xas_store_json)

resources.update(
    {
        "xas": Resource(
            xas_store,
            XASDoc,
            query_operators=[
                FormulaQuery(),
                XASQuery(),
                PaginationQuery(),
                SparseFieldsQuery(
                    XASDoc,
                    default_fields=[
                        "xas_id",
                        "task_id",
                        "edge",
                        "absorbing_element",
                        "formula_pretty",
                        "spectrum_type",
                        "last_updated",
                    ],
                ),
            ],
        )
    }
)

api = MAPI(resources=resources)
app = api.app
