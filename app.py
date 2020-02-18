import os
from monty.serialization import loadfn, dumpfn
from fastapi import FastAPI
from mp_api.xas.models import XASDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery
from mp_api.xas.query_operator import XASQuery

from mp_api.core.resource import Resource

xas_store = os.environ.get("XAS_STORE", "xas_store.json")
xas_store = loadfn(xas_store)

xas_resource = Resource(
    xas_store,
    XASDoc,
    query_operators=[
        FormulaQuery(),
        XASQuery(),
        PaginationQuery(),
        SparseFieldsQuery(
            XASDoc,
            default_fields=["task_id", "edge", "absorbing_element", "last_updated"],
        ),
    ],
)

dumpfn(xas_resource, "xas_resource.json")

app = FastAPI(title="Materials Project API", version="3.0.0-dev")
app.include_router(xas_resource.router)
