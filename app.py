import os
from monty.serialization import loadfn
from mp_api.xas.models import XASDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery
from mp_api.xas.query_operator import XASQuery

from mp_api.core.resource import Resource
from mp_api.core.api import MAPI


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

app = api.app
