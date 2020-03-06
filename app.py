import os
from monty.serialization import loadfn
from fastapi import FastAPI
from mp_api.xas.models import XASDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery
from mp_api.xas.query_operator import XASQuery

from mp_api.core.resource import Resource
from mp_api.core.api import MAPI

xas_store = os.environ.get("XAS_STORE", "xas_store.json")
xas_store = loadfn(xas_store)

api = MAPI(
    resources={
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
                        "edge",
                        "absorbing_element",
                        "spectrum_type",
                        "last_updated",
                    ],
                ),
            ],
        )
    }
)

app = api.app
