from mp_api.core.resource import Resource
from mp_api.xas.models import XASDoc

from mp_api.core.query_operator import PaginationQuery, SparseFieldsQuery
from mp_api.materials.query_operators import FormulaQuery
from mp_api.xas.query_operator import XASQuery


def xas_resource(xas_store):
    resource = Resource(
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
        tags=["XAS"],
    )

    return resource

