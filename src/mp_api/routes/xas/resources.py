from maggma.api.resource import ReadOnlyResource
from emmet.core.xas import XASDoc

from maggma.api.query_operator import PaginationQuery, SortQuery, SparseFieldsQuery
from mp_api.routes.materials.query_operators import ElementsQuery, FormulaQuery
from mp_api.routes.xas.query_operators import XASQuery, XASTaskIDQuery


def xas_resource(xas_store):
    resource = ReadOnlyResource(
        xas_store,
        XASDoc,
        query_operators=[
            FormulaQuery(),
            ElementsQuery(),
            XASQuery(),
            XASTaskIDQuery(),
            SortQuery(),
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
        disable_validation=True,
    )

    return resource
